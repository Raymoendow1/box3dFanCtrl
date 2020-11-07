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

        self.FanConfig = ko.observable();
        self.fan_speed = ko.observable("");
        self.box3d_temp = ko.observable("");
        self.box3d_tartemp = ko.observable("");
        self.fil_trsprt_s = ko.observable("");

        // Test
        self.username = ko.observable("");
        self.password = ko.observable("");
        self.UserNickName = ko.observable();
        self.UserPassword = ko.observable();
        self.login = ko.observable();

        self.slidVal = ko.observable(); //unused
        self.LightColorRed = ko.observable(); //unused
        self.LightColorGreen = ko.observable(); //unused
        self.LightColorBlue = ko.observable(); //unused


        // get data from python-file (only usefull for init)
        self.bindFromSettings = function() {
            // self.slidVal(self.settings.settings.plugins.box3dFanCtrl.slidVal());
            self.FanConfig(self.settings.settings.plugins.box3dFanCtrl.FanConfig());
            self.fan_speed(self.settings.settings.plugins.box3dFanCtrl.fan_speed());
            self.box3d_tartemp(self.settings.settings.plugins.box3dFanCtrl.box3d_tartemp());
            self.box3d_temp(self.settings.settings.plugins.box3dFanCtrl.box3d_temp());

            self.fil_trsprt_s(self.settings.settings.plugins.box3dFanCtrl.fil_trsprt_s());

            // self.UserNickName(self.settings.settings.plugins.box3dFanCtrl.UserNickName());
            // self.UserPassword(self.settings.settings.plugins.box3dFanCtrl.UserPassword());
            self.login(self.settings.settings.plugins.box3dFanCtrl.login());

            self.LightColorRed(self.settings.settings.plugins.box3dFanCtrl.LightColorRed());
            self.LightColorGreen(self.settings.settings.plugins.box3dFanCtrl.LightColorGreen());
            self.LightColorBlue(self.settings.settings.plugins.box3dFanCtrl.LightColorBlue());
        }

        self.onBeforeBinding = function() {
            self.bindFromSettings();
        };

        self.onSettingsBeforeSave = function() {
            self.settings.settings.plugins.box3dFanCtrl.login(self.login());

            self.settings.settings.plugins.box3dFanCtrl.fil_trsprt_s(self.fil_trsprt_s());

            self.settings.settings.plugins.box3dFanCtrl.fan_speed(self.fan_speed());
            self.settings.settings.plugins.box3dFanCtrl.box3d_tartemp(self.box3d_tartemp());
            self.settings.settings.plugins.box3dFanCtrl.box3d_temp(self.box3d_temp());
        };

        self.onSettingsShown = function() {
            self.settings.settings.plugins.box3dFanCtrl.login(self.login());
        };

        // #################### LOG IN/OUT TEST ############################
        self.LogIn = function(item, form) {
            if (self.username() === self.settings.settings.plugins.box3dFanCtrl.UserNickName() && (self.password() === self.settings.settings.plugins.box3dFanCtrl.UserPassword())) {
                self.login(true);
            } else
                new PNotify({
                    title: "box3d Industrial",
                    text: "Wrong username or password",
                    type: "error"
                });
        };

        // Clear username and password
        self.LogOut = function(item, form) {
            self.username("");
            self.password("");
            self.login(false);
        };


        // #################### FAN CONTROL ############################
        self.tempinterval = setInterval(function(item, form) {
            var request = {
                "box3d_temp": self.box3d_temp(),
                "FanSpd": self.fan_speed(),
                "FanCrl": self.FanConfig(),
                "TargTemp": self.box3d_tartemp()
            };
            $.ajax({
                url: self.buildPluginUrl("/getTemperature"),
                type: "GET",
                data: request,
                dataType: "json",
                // success: function(data) {
                //     new PNotify({
                //         title: "box3d Industrial",
                //         text: "New temp " + self.box3d_temp() + " measured",
                //         type: "success"
                //     });
                // }
            });
        }, 500);

        // #################### LED CONTROL ############################
        self.ROn = function(item, form) {
            var request = {
                "color": "red",
                "state": true
            };
            $.ajax({
                type: "POST",
                dataType: "json",
                data: request,
                url: self.buildPluginUrl("/toggleLight"),
                success: function(data) {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Red light set to " + true + " succesfully\n",
                        type: "success"
                    });
                }
            });
        };

        self.GOn = function(item, form) {
            var request = {
                "color": "green",
                "state": true
            };
            $.ajax({
                type: "POST",
                dataType: "json",
                data: request,
                url: self.buildPluginUrl("/toggleLight"),
                success: function(data) {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Green light set to " + true + " succesfully\n",
                        type: "success"
                    });
                }
            });
        };
        self.BOn = function(item, form) {
            var request = {
                "color": "blue",
                "state": true
            };
            $.ajax({
                type: "POST",
                dataType: "json",
                data: request,
                url: self.buildPluginUrl("/toggleLight"),
                success: function(data) {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Blue light set to " + true + " succesfully\n",
                        type: "success"
                    });
                }
            });
        };

        self.ROff = function(item, form) {
            var request = {
                "color": "red",
                "state": false
            };
            $.ajax({
                type: "POST",
                dataType: "json",
                data: request,
                url: self.buildPluginUrl("/toggleLight"),
                success: function(data) {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Red light set to " + false + " succesfully\n",
                        type: "success"
                    });
                }
            });
        };

        self.GOff = function(item, form) {
            var request = {
                "color": "green",
                "state": false
            };
            $.ajax({
                type: "POST",
                dataType: "json",
                data: request,
                url: self.buildPluginUrl("/toggleLight"),
                success: function(data) {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Blue light set to " + false + " succesfully\n",
                        type: "success"
                    });
                }
            });
        };

        self.BOff = function(item, form) {
            var request = {
                "color": "blue",
                "state": false
            };
            $.ajax({
                type: "POST",
                dataType: "json",
                data: request,
                url: self.buildPluginUrl("/toggleLight"),
                success: function(data) {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Green light set to " + false + " succesfully\n",
                        type: "success"
                    });
                }
            });
        };

        // Change the lights received from HTML button
        self.killBlink = function() {
            $.ajax({
                url: self.buildPluginUrl("/KillBlink"),
                type: "POST",
                dataType: "json",
                success: function(data) {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Blink has been killed",
                        type: "success"
                    });
                }
            });
        };

        // ###################### 			LOCK CTRL				##################################
        self.Unlock = function() {
            var request = {
                "temperature": self.box3d_temp()
            };
            $.ajax({
                url: self.buildPluginUrl("/unlock"),
                type: "POST",
                data: request,
                dataType: "json",
                success: function() {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Unlocked!",
                        type: "success"
                    });
                }
            });
        };
        self.Lock = function() {
            $.ajax({
                url: self.buildPluginUrl("/lock"),
                type: "POST",
                dataType: "json",
                success: function() {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Locked!",
                        type: "success"
                    });
                }
            });
        };

        // #################### FILAMENT LOADING #############################
        self.filament = function() {
            var request = {
                "fil_transport_state": self.fil_trsprt_s()
            };
            $.ajax({
                url: self.buildPluginUrl("/LoadFilament"),
                type: "POST",
                data: request,
                dataType: "json",
                success: function() {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Filament state (variable): " + String(self.fil_trsprt_s()),
                        type: "success"
                    });
                },
                error: function() {
                    new PNotify({
                        title: "box3d Industrial",
                        text: "Print still in progress",
                        type: "error"
                    });
                }
            });
        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (typeof plugin == 'undefined') {
                return;
            }

            if (plugin != "box3dFanCtrl") {
                return;
            }

            if (self.settingsOpen) {
                return;
            }

            if (data.hasOwnProperty("comptemp"))
                if (data.comptemp)
                    self.box3d_temp(_.sprintf("%d", data.comptemp));

            if (data.hasOwnProperty("fan"))
                if (data.fan)
                    self.fan_speed(_.sprintf("%d", data.fan))

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
        elements: ["#tab_plugin_box3dFanCtrl" /*, "#settings_plugin_box3dFanCtrl" /*, "#navbar_plugin_box3dFanCtrl"*/ ]
    });
});