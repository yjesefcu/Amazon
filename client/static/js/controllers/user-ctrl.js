"use strict";
/**
 * Created by liucaiyun on 2018/1/6.
 */
app.controller('UserCtrl', function($scope, $http, $rootScope) {

    $scope.users = [];

    function getUsers() {
        $http.get('/api/users/').then(function (result) {
            $scope.users = result.data;
        }).catch(function (error) {
            $rootScope.addAlert('error', '获取用户失败');
        });
    }

    $scope.createUser = function () {

        // var modalInstance = $uibModal.open({
        //     templateUrl : '/static/templates/users/user_create.html',//script标签中定义的id
        //     controller : 'UserCreateCtrl',//modal对应的Controller
        // });
        $scope.$broadcast('create');
    };

    $scope.deleteUser = function (userId) {
        $http.delete('/api/users/' + userId + '/').then(function (result) {
            $rootScope.addAlert('info', '删除用户成功');
            getUsers();
        }).catch(function (error) {
            $rootScope.addAlert('error', '删除用户失败');
        });
    };

    $scope.refresh = function () {
        getUsers();
    };

    getUsers();
});

app.controller('UserCreateCtrl', function($scope, $http, $rootScope) {
    $scope.user = {};

    $scope.submit = function () {
        if ($scope.userForm.$invalid) {
            return;
        }
        $http.post('/api/users/', $scope.user).then(function (result) {
            $rootScope.addAlert('info', '用户添加成功');
            $scope.$parent.refresh();
            $scope.close();
        }).catch(function (exception) {
            $rootScope.addAlert('error', '用户添加失败');
        });
        return false;
    };

    $scope.close = function () {
        // $uibModalInstance.close();
        $scope.user = {};
        $("#userModal").modal('hide');
    };

    $scope.$on('create', function () {
        $scope.user = {};
         $("#userModal").modal('show');
    });
});
