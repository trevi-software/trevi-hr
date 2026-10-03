import {Component, onMounted, onWillUnmount, useRef, useState} from "@odoo/owl";
import {ImageField, imageField} from "@web/views/fields/image/image_field";
import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

/**
 * Modal showing the live webcam feed. The camera is switched on when the
 * dialog opens and released whenever it closes, however it is closed.
 */
export class PhotoboothDialog extends Component {
    static template = "hr_photobooth.PhotoboothDialog";
    static components = {Dialog};
    static props = {
        close: Function,
        onCapture: Function,
    };

    setup() {
        this.videoRef = useRef("video");
        this.state = useState({ready: false, error: ""});
        this.stream = null;
        this.closed = false;
        onMounted(() => this.startCamera());
        onWillUnmount(() => {
            this.closed = true;
            this.stopCamera();
        });
    }

    get title() {
        return _t("Photo Booth");
    }

    async startCamera() {
        // Browsers only expose mediaDevices in a secure context (HTTPS or localhost).
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.state.error = _t(
                "The browser does not allow camera access on this page. " +
                    "Open Odoo over HTTPS (or on localhost) to use the photo booth."
            );
            return;
        }
        let stream = null;
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false,
            });
        } catch (error) {
            if (!this.closed) {
                this.state.error = this.describeError(error);
            }
            return;
        }
        if (this.closed) {
            // The dialog was closed while the permission prompt was open.
            stream.getTracks().forEach((track) => track.stop());
            return;
        }
        this.stream = stream;
        if (this.videoRef.el) {
            this.videoRef.el.srcObject = stream;
        }
    }

    describeError(error) {
        switch (error && error.name) {
            case "NotAllowedError":
            case "SecurityError":
                return _t(
                    "Camera access was denied. Allow this site to use the camera in the browser settings and try again."
                );
            case "NotFoundError":
            case "OverconstrainedError":
                return _t("No camera was found. Check that a webcam is connected.");
            case "NotReadableError":
                return _t(
                    "The camera could not be started. It may be in use by another application."
                );
            default:
                return _t(
                    "The camera could not be started: %s",
                    error && error.message
                );
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
            this.stream = null;
        }
    }

    onVideoReady() {
        // Fired once the first frame is available; capturing earlier could
        // produce a blank image even if videoWidth/videoHeight are known.
        this.state.ready = true;
    }

    capture() {
        const video = this.videoRef.el;
        if (!this.state.ready || !video || !video.videoWidth) {
            return;
        }
        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
        // Strip the "data:image/jpeg;base64," prefix: Odoo stores raw base64.
        const data = canvas.toDataURL("image/jpeg", 0.92).split(",")[1];
        this.props.onCapture(data);
        this.props.close();
    }
}

/**
 * The standard image widget (preview, upload, clear, zoom) with an extra
 * button that takes the picture with the webcam.
 */
export class CameraCaptureField extends ImageField {
    static template = "hr_photobooth.CameraCaptureField";

    setup() {
        super.setup();
        this.dialog = useService("dialog");
    }

    openPhotobooth() {
        this.dialog.add(PhotoboothDialog, {
            onCapture: (data) =>
                this.onFileUploaded({
                    data,
                    name: "photo.jpg",
                    type: "image/jpeg",
                }),
        });
    }
}

registry.category("fields").add("camera_capture", {
    ...imageField,
    component: CameraCaptureField,
});
