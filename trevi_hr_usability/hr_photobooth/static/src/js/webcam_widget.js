/**
 * Copyright 2021 TREVI Software <support@trevi.et>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
 *
 */

odoo.define("hr_photobooth.webcam_widget", function (require) {
    "use strict";

    const IMG_WIDTH = 320;
    const IMG_HEIGHT = 240;
    const framework = require("web.framework");
    const rpc = require("web.rpc");
    const Widget = require("web.Widget");
    const widgetRegistry = require("web.widget_registry");

    var WebcamWidget = Widget.extend({
        template: "photo.action",
        xmlDependencies: ["/hr_photobooth/static/src/xml/webcam_widget.xml"],
        events: {
            "click .webcam_snap": "onClickSnap",
            "click .webcam_close": "onClickSaveClose",
            "click .webcam_cancel": "onClickCancel",
        },

        /**
         * @override
         */
        init: function (parent, record, nodeInfo) {
            this._super.apply(this, arguments);
            this.res_model = nodeInfo.attrs.dst_model;
            this.res_field = nodeInfo.attrs.dst_field;
            this.res_id = record.data.employee_id.res_id;
            this.flagStream = false;
        },

        /**
         * @override
         */
        start: function () {
            var self = this;
            var $video = this.$("video.webcam_video");

            if (navigator.mediaDevices) {
                navigator.mediaDevices
                    .getUserMedia({video: true, audio: false})
                    .then(function (mediaStream) {
                        $video[0].srcObject = mediaStream;
                        self.flagStream = true;
                    })
                    .catch(function (err) {
                        console.log(err.name + " : " + err.message);
                    });
            }
        },

        onClickSnap: function (event) {
            event.preventDefault();
            event.stopPropagation();
            var $video = this.$("video.webcam_video");
            var $canvas = this.$("canvas.webcam_canvas");
            var ctx = $canvas[0].getContext("2d");
            ctx.drawImage($video[0], 0, 0, IMG_WIDTH, IMG_HEIGHT);
            this.$(".webcam_close").removeAttr("disabled");
        },

        onClickSaveClose: function (event) {
            event.preventDefault();
            event.stopPropagation();
            var $canvas = this.$("canvas.webcam_canvas");
            var imgData = $canvas[0]
                .toDataURL("image/png")
                .replace(/^data:image\/(png|jpg);base64,/, "");

            var $video = this.$("video.webcam_video");
            var mediaStream = $video[0].srcObject;
            var mediaTracks = mediaStream.getTracks();
            for (var i = 0; i < mediaTracks.length; i++) {
                mediaTracks[i].stop();
            }
            $video.srcObject = null;

            const always = () => {
                this.trigger_up("reload");
                framework.unblockUI();
                this.trigger_up("close_dialog");
            };
            framework.blockUI();
            var vals = {};
            vals[this.res_field] = imgData;
            const rpcProm = rpc.query({
                method: "write",
                model: this.res_model,
                args: [this.res_id, vals],
            });
            rpcProm.then(always).guardedCatch(always);
            return rpcProm;
        },

        onClickCancel: function (event) {
            event.preventDefault();
            event.stopPropagation();
            var $video = this.$("video.webcam_video");
            var mediaStream = $video[0].srcObject;
            var mediaTracks = mediaStream.getTracks();
            for (var i = 0; i < mediaTracks.length; i++) {
                mediaTracks[i].stop();
            }
            $video.srcObject = null;
            this.trigger_up("close_dialog");
        },
    });

    widgetRegistry.add("webcam_widget", WebcamWidget);
    return WebcamWidget;
});
