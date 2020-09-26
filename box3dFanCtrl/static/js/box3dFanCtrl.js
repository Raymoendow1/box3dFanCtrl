/*
 * View model for box3dFanCtrl
 *
 * Author: Raymond de Hooge
 * License: AGPLv3
 */
$(function() {
    function Box3dfanctrlViewModel(parameters) {
        var self = this;
        self.pluginName = "box3dFanCtrl";

        self.settings = parameters[0];
        self.slidVal = ko.observable();
        self.slidCheck = ko.observable(false);


        self.onBeforeBinding = function() {
            self.slidVal(self.settings.settings.plugins.box3dFanCtrl.slidVal());
            // self.slidCheck(self.settings.settings.plugins.box3dFanCtrl.slidCheck());
        }


        self.setFan = function(item, form) {
            var request = {
                "status": item.slidVal()
            };
            $.ajax({
                type: "GET",
                dataType: "json",
                data: request,
                url: self.buildPluginUrl("/setFAN"),
                success: function(data) {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Fanspeed set to " + item.slidVal() + " succesfully",
                        type: "success"
                    });
                }
            });

        };

        self.buildPluginUrl = function(path) {
            return window.PLUGIN_BASEURL + self.pluginName + path;
        };
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: Box3dfanctrlViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ /* "loginStateViewModel",*/ "settingsViewModel"],
        // Elements to bind to, e.g. #settings_plugin_box3dFanCtrl, #tab_plugin_box3dFanCtrl, ...
        elements: ["#tab_plugin_box3dFanCtrl" /*, "#settings_plugin_box3dFanCtrl" *, "#navbar_plugin_box3dFanCtrl"*/ ]
    });
});