import {Component, xml} from "@odoo/owl";
import {
    click,
    manuallyDispatchProgrammaticEvent,
    queryFirst,
    waitFor,
    waitForNone,
} from "@odoo/hoot-dom";
import {
    clickSave,
    defineModels,
    fields,
    models,
    mountView,
    mountWithCleanup,
    onRpc,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";
import {expect, test} from "@odoo/hoot";
import {PhotoboothDialog} from "@hr_photobooth/js/webcam_widget.esm";
import {animationFrame} from "@odoo/hoot-mock";
import {defineMailModels} from "@mail/../tests/mail_test_helpers";
import {useService} from "@web/core/utils/hooks";

const CAPTURED_IMAGE = "CAPTURED_IMAGE";
const DENIED_MESSAGE =
    "Camera access was denied. Allow this site to use the camera in the browser settings and try again.";
const BUSY_MESSAGE =
    "The camera could not be started. It may be in use by another application.";
const MISSING_MESSAGE = "No camera was found. Check that a webcam is connected.";
const INSECURE_MESSAGE =
    "The browser does not allow camera access on this page. " +
    "Open Odoo over HTTPS (or on localhost) to use the photo booth.";

class HrEmployee extends models.Model {
    _name = "hr.employee";

    image_1920 = fields.Binary();

    _records = [{id: 1}];
}

// The test environment starts every registered service, including mail's store
// and discuss' rtc, which query discuss.channel and friends
defineMailModels();
defineModels([HrEmployee]);

/** Does nothing, for the places that need a callable and nothing else. */
const noop = () => undefined;

/** A real MediaStream (the video element refuses anything else) holding one fake track. */
function makeStream() {
    const track = {
        stopped: false,
        stop() {
            this.stopped = true;
        },
    };
    const stream = new MediaStream();
    stream.getTracks = () => [track];
    return {stream, track};
}

/**
 * Replace the camera for the current test only.
 *
 * The whole `mediaDevices` object is swapped: headless Chrome answers with a
 * fake camera of its own, and the module reads `navigator.mediaDevices` again
 * on every call.
 */
function mockCamera(getUserMedia) {
    patchWithCleanup(navigator, {mediaDevices: {getUserMedia}});
}

/** A canvas that always "captures" the same picture. */
function mockCanvas() {
    patchWithCleanup(HTMLCanvasElement.prototype, {
        getContext: () => ({drawImage: noop}),
        toDataURL: () => `data:image/jpeg;base64,${CAPTURED_IMAGE}`,
    });
}

/** Give the (fake) video element a picture size. */
function setVideoSize(video, width = 640, height = 480) {
    Object.defineProperty(video, "videoWidth", {value: width, configurable: true});
    Object.defineProperty(video, "videoHeight", {value: height, configurable: true});
}

/**
 * The dialog is always opened through the dialog service, which is how the
 * field opens it: the Dialog component reads `env.dialogData` from there.
 */
class PhotoboothHost extends Component {
    static template = xml`<div class="o_photobooth_host"/>`;
    static props = ["*"];

    setup() {
        this.dialog = useService("dialog");
    }

    openPhotobooth(onCapture) {
        this.dialog.add(PhotoboothDialog, {onCapture});
    }
}

/** Mounts the host and opens the dialog (no wait: it may show an error instead). */
async function mountPhotobooth(onCapture = noop) {
    const host = await mountWithCleanup(PhotoboothHost);
    host.openPhotobooth(onCapture);
    return host;
}

/** Opens the dialog and waits for the live video. */
async function openPhotobooth(onCapture = noop) {
    const host = await mountPhotobooth(onCapture);
    await waitFor(".o_photobooth_video");
    return host;
}

/** Waits for the first frame and leaves the capture button ready. */
async function waitUntilReady() {
    const video = queryFirst(".o_photobooth_video");
    setVideoSize(video);
    await manuallyDispatchProgrammaticEvent(video, "loadeddata");
    await waitFor(".o_photobooth_capture:enabled");
}

test("a denied camera permission is reported in the dialog", async () => {
    mockCamera(() => Promise.reject(new DOMException("denied", "NotAllowedError")));

    await mountPhotobooth();
    await waitFor(".o_photobooth_error");

    expect(".o_photobooth_error").toHaveText(DENIED_MESSAGE);
    expect(".o_photobooth_video").toHaveCount(0);
    expect(".o_photobooth_capture").not.toBeEnabled();
});

test("a camera that cannot be started is reported in the dialog", async () => {
    mockCamera(() => Promise.reject(new DOMException("busy", "NotReadableError")));

    await mountPhotobooth();
    await waitFor(".o_photobooth_error");

    expect(".o_photobooth_error").toHaveText(BUSY_MESSAGE);
});

test("a missing camera is reported in the dialog", async () => {
    mockCamera(() => Promise.reject(new DOMException("no device", "NotFoundError")));

    await mountPhotobooth();
    await waitFor(".o_photobooth_error");

    expect(".o_photobooth_error").toHaveText(MISSING_MESSAGE);
});

test("a browser without a camera API is reported in the dialog", async () => {
    // No getUserMedia at all, which is what an insecure context looks like
    patchWithCleanup(navigator, {mediaDevices: {}});

    await mountPhotobooth();
    await waitFor(".o_photobooth_error");

    expect(".o_photobooth_error").toHaveText(INSECURE_MESSAGE);
});

test("closing the dialog while the permission prompt is open releases the camera", async () => {
    const {stream, track} = makeStream();
    let resolveStream = null;
    mockCamera(() => new Promise((resolve) => (resolveStream = resolve)));

    await openPhotobooth();

    // Cancel while the browser is still waiting for the user's answer
    await click(".modal-footer .btn-secondary");
    await waitForNone(".o_photobooth_video");

    resolveStream(stream);
    await animationFrame();

    expect(track.stopped).toBe(true, {
        message: "the camera must not be left running after the dialog is gone",
    });
});

test("the picture can only be taken once the first frame is ready", async () => {
    const {stream} = makeStream();
    mockCamera(() => Promise.resolve(stream));
    mockCanvas();

    let captured = null;
    await openPhotobooth((data) => (captured = data));

    // The stream is attached, but no frame has arrived yet
    expect(queryFirst(".o_photobooth_video")).toHaveProperty("srcObject", stream);
    expect(".o_photobooth_capture").not.toBeEnabled();
    expect(captured).toBe(null);

    await waitUntilReady();
    await click(".o_photobooth_capture");

    expect(captured).toBe(CAPTURED_IMAGE);
    await waitForNone(".o_photobooth_video");
});

test("capturing without any picture in the video does nothing", async () => {
    mockCamera(() => Promise.resolve(makeStream().stream));
    mockCanvas();

    let captured = null;
    await openPhotobooth((data) => (captured = data));

    const video = queryFirst(".o_photobooth_video");
    setVideoSize(video, 0, 0);
    await manuallyDispatchProgrammaticEvent(video, "loadeddata");
    await waitFor(".o_photobooth_capture:enabled");

    await click(".o_photobooth_capture");

    expect(captured).toBe(null);
    expect(".o_photobooth_video").toHaveCount(1, {message: "the dialog stays open"});
});

test("taking a photo updates the employee image", async () => {
    mockCamera(() => Promise.resolve(makeStream().stream));
    mockCanvas();

    let savedImage = null;
    onRpc("web_save", ({args}) => {
        savedImage = args[1].image_1920;
    });

    await mountView({
        type: "form",
        resModel: "hr.employee",
        resId: 1,
        arch: `
            <form>
                <field name="image_1920" widget="camera_capture"/>
            </form>
        `,
    });

    await click(".o_photobooth_button");
    await waitFor(".o_photobooth_video");

    await waitUntilReady();
    await click(".o_photobooth_capture");
    await waitForNone(".o_photobooth_video");

    await clickSave();
    expect(savedImage).toBe(CAPTURED_IMAGE);
});
