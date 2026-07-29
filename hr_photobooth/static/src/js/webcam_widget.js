/** @odoo-module **/

import { Component, useRef, onWillDestroy } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { registry } from "@web/core/registry";

export class CameraCaptureField extends Component {
    static template = "hr_photobooth.CameraCaptureField";
    static props = { ...standardFieldProps };

    setup() {
        this.videoRef = useRef("video");
        this.canvasRef = useRef("canvas");
        this.stream = null;
    }

    // 1. Start Webcam Stream
    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ video: true });
            if (this.videoRef.el) {
                this.videoRef.el.srcObject = this.stream;
            }
        } catch (error) {
            console.error("Camera access denied or unavailable:", error);
        }
    }

    // 2. Capture and Save Photo
    capturePhoto() {
        const video = this.videoRef.el;
        const canvas = this.canvasRef.el;
        if (!video || !canvas) return;

        const context = canvas.getContext("2d");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Draw current video frame onto canvas
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert canvas image to Base64 (Odoo's binary format)
        const dataUrl = canvas.toDataURL("image/jpeg");
        const base64Data = dataUrl.split(",")[1]; // Strip the data:image/jpeg;base64 prefix

        // Write data directly to the Odoo field
        this.props.record.update({ [this.props.name]: base64Data });

        this.stopCamera();
    }

    // 3. Stop Webcam Stream
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    onWillDestroy() {
        this.stopCamera();
    }
}

// Register the field widget in Odoo's fields registry
registry.category("fields").add("camera_capture", {
    component: CameraCaptureField,
    supportedTypes: ["binary"],
});
