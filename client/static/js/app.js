"use strict";
/**
 * Created by liucaiyun on 2017/5/4.
 */

var app = angular.module('myApp', ['ui.router', 'atomic-notify', 'ui.bootstrap', '720kb.datepicker']);

app.controller('MainCtrl', function ($scope, $state, $http, $rootScope, $location, serviceFactory) {
    $rootScope.currentMarket = {'country': '公共'};
    $rootScope.MarketplaceId = 'public' ;
    $rootScope.alerts = [];
    $rootScope.markets = [];
    $rootScope.currentcy = 'USD';
    $scope.currentUrl = $location.$$path;
    $rootScope.addAlert = function (type, msg, timeout) {
        if (typeof(timeout) === 'undefined'){
            timeout = 3000;
        }
        $rootScope.alerts.push({
            type: type, msg: msg, "dismiss-on-timeout": timeout, close: function () {
                return $rootScope.closeAlert(this);
            }
        });
    };

    function getAllAccounts() {
        $http.get('/api/markets').then(function (result) {
            $rootScope.markets = result.data;
        });
    }
    $rootScope.closeAlert = function (index) {
        $rootScope.alerts.splice(index, 1);
    };

    $http.get(serviceFactory.markets())
        .then(function (result) {
             $rootScope.markets = result.data;
             $rootScope.currentMarket = result.data[0];
             $rootScope.currency = $rootScope.currentMarket.currency;
        });

    $scope.chooseMarket = function (index) {
        $rootScope.currentMarket = $rootScope.markets[index];
        $rootScope.MarketplaceId = $rootScope.currentMarket.MarketplaceId;
        $rootScope.currency = $rootScope.currentMarket.currency;
        $state.go('index');
    };

    function getPermission() {
        $http.get('/permissions').then(function (result) {
            var data = result.data;
            $rootScope.user = data.user;
            $rootScope.userRole = data.role;
            $rootScope.permissions = data.permissions;
        });
    }

    $scope.chooseMenu = function (url) {
        $scope.currentUrl = url;
    };

    getAllAccounts();
    getPermission();
});

app.config(['atomicNotifyProvider', function(atomicNotifyProvider){

    // atomicNotifyProvider.setDefaultDelay(5000);
    // atomicNotifyProvider.useIconOnNotification(true);

}]);

app.config(function($sceDelegateProvider) {
    $sceDelegateProvider.resourceUrlWhitelist([
        // Allow same origin resource loads.
        '**']);
});

// $.fn.dataTables.ext.errMode = 'none'; //不显示任何错误信息

app.directive("submitButton", function () {
    return {
     　　template: '<div></div>',
     　　templateUrl: 'directive.html',
     　　restrict: 'E',
     　　scope: false,
     　　compile: function compile(tElement, tAttrs, transclude) {

     　　　　return {
     　　　　　　pre: function preLink(scope, iElement, iAttrs, controller) {

               },

         　　　　　　post: function postLink(scope, iElement, iAttrs, controller) {

               }
    　　　　}
    　　 },
     　　link: function postLink(scope, iElement, iAttrs) {

       }

    };
});