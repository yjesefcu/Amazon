"use strict";
/**
 * Created by liucaiyun on 2017/5/22.
 */

app.controller('HomeCtrl', function($scope) {
    $scope.firstName = "John";
    $scope.lastName = "Doe";
    $scope.fullName = function() {
        return $scope.firstName + " " + $scope.lastName;
    }
});
