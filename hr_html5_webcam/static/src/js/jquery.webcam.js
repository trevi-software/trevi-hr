/**
 * @license jQuery webcam plugin v1.0 09/12/2010
 * http://www.xarg.org/project/jquery-webcam-plugin/
 *
 * Copyright (c) 2010, Robert Eisele (robert@xarg.org)
 * Dual licensed under the MIT or GPL Version 2 licenses.
 **/

(function ($) {
    "use strict";

    var webcam = {
        // External select token to support jQuery dialogs
        extern: null,
        // Append object instead of overwriting
        append: true,

        width: 320,
        height: 240,

        // Callback | save | stream
        mode: "callback",

        swffile: "jscam.swf",
        quality: 85,
    };

    window.webcam = webcam;

    $.fn.webcam = function (options) {
        if (typeof options === "object") {
            for (var ndx in webcam) {
                if (options[ndx] !== undefined) {
                    webcam[ndx] = options[ndx];
                }
            }
        }

        var source =
            '<object id="XwebcamXobjectX" type="application/x-shockwave-flash" data="' +
            webcam.swffile +
            '" width="' +
            webcam.width +
            '" height="' +
            webcam.height +
            '"><param name="movie" value="' +
            webcam.swffile +
            '" /><param name="FlashVars" value="mode=' +
            webcam.mode +
            "&amp;quality=" +
            webcam.quality +
            '" /><param name="allowScriptAccess" value="always" /></object>';

        if (webcam.extern !== null) {
            $(webcam.extern)[webcam.append ? "append" : "html"](source);
        } else {
            this[webcam.append ? "append" : "html"](source);
        }

        var _register = (function (run) {
            var cam = document.getElementById("XwebcamXobjectX");

            if (cam.capture !== undefined) {
                /* Simple callback methods are not allowed :-/ */
                webcam.capture = function (x) {
                    try {
                        return cam.capture(x);
                    } catch (e) {
                        // Pass
                    }
                };
                webcam.save = function (x) {
                    try {
                        return cam.save(x);
                    } catch (e) {
                        // Pass
                    }
                };
                webcam.setCamera = function (x) {
                    try {
                        return cam.setCamera(x);
                    } catch (e) {
                        // Pass
                    }
                };
                webcam.getCameraList = function () {
                    try {
                        return cam.getCameraList();
                    } catch (e) {
                        // Pass
                    }
                };

                webcam.onLoad();
            } else if (run === 0) {
                webcam.debug("error", "Flash movie not yet registered!");
            } else {
                /* Flash interface not ready yet */
                window.setTimeout(_register, 1000 * (4 - run), run - 1);
            }
        })(3);
    };
})(jQuery);
