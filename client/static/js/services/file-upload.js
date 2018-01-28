"use strict";
/**
 * Created by liucaiyun on 2017/6/19.
 */

app.directive('fileModel', ['$parse', function ($parse) {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            var model = $parse(attrs.fileModel);
            var modelSetter = model.assign;

            element.bind('change', function(){
                scope.$apply(function(){
                    modelSetter(scope, element[0].files[0]);
                });
            });
        }
    };
}]);

app.service('fileUpload', ['$http', '$rootScope', function ($http, $rootScope) {
    this.uploadFileToUrl = function(file, uploadUrl, cb, finally_cb){
        var fd = new FormData();
        fd.append('file', file);

        $http.post(uploadUrl, fd, {
            transformRequest: angular.identity,
            headers: {'Content-Type': undefined}
        }).then(function(result){
            cb && cb(result.data);
        })
        .catch(function(){
            $rootScope.addAlert('error', '上传失败');
        })
            .finally(function(){
                finally_cb && finally_cb();
            });
    }
}]);