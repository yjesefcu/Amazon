"use strict";

app.controller('settlementCtrl', function ($scope, $rootScope, $http, $state, $stateParams, $timeout, $interval, serviceFactory, fileUpload) {
    $scope.settlements = [];
    $scope.selectedSettlement = '';
    $scope.isCalculating = false;
    $scope.calcIndex = 0;
    var calcSettlementId;
    var calcStatusInterval = null;
    $scope.readingReport = 0;       // 0：未同步，1：同步失败，10：正在同步
    var readingReportInterval = null;
    $scope.errorInfo = '';  //  错误信息
    $scope.storageInvalid = false;      // 仓储报告没有上传
    $scope.removalInvalid = false;      // 移除报告没有上传
    $scope.advertisingInvalid = false;      // 广告费没有设置
    $scope.advertising_fee = '';

    var settlementId = $stateParams.id;
    $scope.selected = '';
    if (settlementId){
        $scope.selectedSettlement = parseInt(settlementId);
    }
    getSettlements();
    function getSettlements(){

        $http.get(serviceFactory.settlements(), {
            params: {
                MarketplaceId: $rootScope.MarketplaceId
            }
        }).then(function (result) {
            $scope.settlements = result.data;
        }).catch(function () {
            $rootScope.addAlert('error', '获取结算列表失败')
        });
    }
    $scope.$watch('selectedSettlement', function (newValue, oldValue) {
        console.log('change');
        if (newValue)
        {
            $state.go('index.settlement.detail', {id: newValue});
        }
    });

    $scope.startCalculate = function (index, id) {
        calcSettlementId = id;
        checkDataValidation(index, id, function () {
            $http.get(serviceFactory.settlementDetail(id) + 'calc/')
                .then(function (result) {
                    var errno = result.data.errno;
                    $rootScope.addAlert('info', '正在计算，请稍候...');
                    $scope.settlements[index]['calc_status'] = errno ? 1 : 10;
                    clacStatusCheckingInterval(index, id);
                }).catch(function (result) {
                $scope.settlements[index]['calc_status'] = 10;
                $rootScope.addAlert('error', '启动计算失败');
            });
        });
    };

    $scope.startReadingReport = function () {

         $http.get(serviceFactory.settlements() + 'sync/', {
             params: {
                 MarketplaceId: $rootScope.MarketplaceId
             }
         }).then(function (result) {
             if (!readingReportInterval){
                 readingReportInterval = $interval(function () {
                     console.log('query getting report status');
                     $http.get(serviceFactory.settlements() + 'syncStatus/', {
                         params: {
                             MarketplaceId: $rootScope.MarketplaceId
                         }}).then(function (result) {
                             var errno = result.data.errno;
                             $scope.readingReport = errno;
                             if (errno == 0){
                                 $rootScope.addAlert('info', '同步完成');
                                 getSettlements();
                             }else if (errno == 1){
                                 $rootScope.addAlert('error', '同步失败');
                             }
                             if (errno == 0 || errno == 1){
                                 $interval.cancel(readingReportInterval);
                                 readingReportInterval = null;
                             }
                             console.log('getting report: ' + result.data.errno);
                     }).catch(function (result) {
                         $scope.readingReport = 1;
                         console.log('query getting report error');
                     });

                 }, 10000);
             }
             $scope.readingReport = 10;
             $rootScope.addAlert('info', '正在同步...请勿关闭系统');
         }).catch(function () {
             $scope.readingReport = 1;
             $rootScope.addAlert('error', '启动失败！')
         })
    };
    $scope.$on('destroy',function(){
        calcStatusInterval && $interval.cancel(calcStatusInterval);
        readingReportInterval && $interval.cancel(readingReportInterval);
        calcStatusInterval = null;
        readingReportInterval = null;
    }) ; //在控制器里，添加$on函数

    $scope.download = function (index, id) {
        $scope.settlements[index].isDownloading = true;
        $http.get(serviceFactory.settlementDetail(id) + 'download/')
            .then(function (result) {
                $rootScope.addAlert('info', '报告已生成');
                $scope.settlements[index].isDownloading = false;
                window.location.href = serviceFactory.downloadPath(result.data.path);
            }).catch(function (result) {
                $scope.settlements[index].isDownloading = false;
                $rootScope.addAlert('error', '报告生成失败');
            });
    };

    function checkDataValidation(index, id, cb) {    // 检查商品订单与库存是否匹配
        $scope.errorInfo = '';
        $scope.calcIndex = index;
        $scope.storageInvalid = false;
        $scope.removalInvalid = false;
        $scope.settlements[index]['calc_status'] = 10;
        $rootScope.addAlert('info', '正在计算数据有效性...');
        $http.get(serviceFactory.settlementDetail(id) + 'check/').then(function (result) {
            var products = result.data.products;
            var isInvalid = false;
            if (!result.data.data_sync_valid){
                isInvalid = true;
                $scope.settlements[index]['calc_status'] = 1;
                $scope.errorInfo = '数据同步时发生错误，请重新执行上面的“同步数据”';
            }else{
                if (products.length)
                {
                    isInvalid = true;
                    $scope.settlements[index]['calc_status'] = 1;
                    $scope.errorInfo = '以下商品所配置的库存与订单中的不符，请添加商品的入库或移库信息后重新计算：' + products;
                }
                if (!result.data.storage_imported){
                    isInvalid = true;
                    $scope.storageInvalid = true;
                }
                if (!result.data.removal_imported){
                    isInvalid = true;
                    $scope.removalInvalid = true;
                }
                if (!result.data.advertising_valid){
                    isInvalid = true;
                    $scope.advertisingInvalid = true;
                }
            }
            if (!isInvalid){
                cb && cb();
            }else{
                $scope.settlements[index]['calc_status'] = 1;
                $scope.settlements[index].is_invalid = true;
            }
        }).catch(function (result) {
            $scope.errorInfo = '';
            $scope.settlements[index]['calc_status'] = 1;
            $rootScope.addAlert('发生异常');
        })

    }
    
    function clacStatusCheckingInterval(index, id) {
        if (!calcStatusInterval){
            calcStatusInterval = $interval(function () {
                console.log('query calculating status');
                $http.get(serviceFactory.settlementDetail(id) + 'calcStatus/').then(function (result) {
                    var errno = result.data.errno;
                    if (errno == 0){
                        $rootScope.addAlert('info', '计算完成');
                        $interval.cancel(calcStatusInterval);
                        calcStatusInterval = null;
                        getSettlements();
                    }else if (errno == 1){
                        $rootScope.addAlert('info', '计算失败');
                        $interval.cancel(calcStatusInterval);
                        calcStatusInterval = null;
                    }
                    $scope.settlements[index]['calc_status'] = errno;
                    console.log('calculating status: ' + errno);
                }).catch(function (result) {
                    console.log('query calculating status error');
                });
            }, 5000);
        }
    }

    // 仓储费和订阅费
    $timeout(function () {
        angular.element("#glbalStorageFile").on('change', function(){
            $scope.glbalStorageFile = this.files[0];
        });
        angular.element("#globalRemovalFile").on('change', function(){
            $scope.globalRemovalFile = this.files[0];
        });
        angular.element("#advertisingFile").on('change', function(){
            $scope.globalAdvertisingFile = this.files[0];
        });
    }, 1000);
    $scope.sendRemovalFile = function(){
        var url = serviceFactory.uploadRemovals(calcSettlementId),
            file = $scope.globalRemovalFile;
        if ( !file ) return;
        fileUpload.uploadFileToUrl(file, url, function (data) {
            if (!data.errno){
                $rootScope.addAlert('success', '上传成功，一共找到' + data.data.length + '条记录');
                $scope.removalInvalid = false;
            }else {
                $rootScope.addAlert('error', '上传失败，请确认上传文件是否移除报告');
            }
        });
    };
    $scope.sendStorageFile = function(){
        var url = serviceFactory.settlementDetail(calcSettlementId) + 'storage_upload/',
            file = $scope.glbalStorageFile;
        if ( !file ) return;
        fileUpload.uploadFileToUrl(file, url, function (data) {
            if (!data.errno){
                $rootScope.addAlert('success', '上传成功，一共找到' + data.data.length + '条记录');
                $scope.storageInvalid = false;
            }else {
                $rootScope.addAlert('error', '上传失败，请确认上传文件是否移除报告');
            }
        });
    };
    $scope.sendAdvertisingFile = function() {   // 上传广告报告
        var url = serviceFactory.settlementDetail(calcSettlementId) + 'advertising_upload/',
            file = $scope.globalAdvertisingFile;
        if ( !file ) return;
        fileUpload.uploadFileToUrl(file, url, function (data) {
            if (!data.errno){
                $rootScope.addAlert('success', '上传成功');
                $scope.storageInvalid = false;
            }else {
                $rootScope.addAlert('error', '上传失败，请确认上传文件是否广告报告');
            }
        });
    };

    $scope.skipStorageReport = function () {
        $http.patch(serviceFactory.settlementDetail(calcSettlementId), {
            storage_imported: 1
        }).then(function (result) {
            $rootScope.addAlert('info', '设置成功');
            $scope.storageInvalid = false;
        }).catch(function (result) {
            $rootScope.addAlert('error', '发生异常');
        });
    };

    $scope.skipRemovalReport = function () {
        $http.patch(serviceFactory.settlementDetail(calcSettlementId), {
            removal_imported: 1
        }).then(function (result) {
            $rootScope.addAlert('info', '设置成功');
            $scope.removalInvalid = false;
        }).catch(function (result) {
            $rootScope.addAlert('error', '发生异常');
        });

    };

    $scope.setAdvertising = function () {
        if ($scope.advertising_fee == ''){
            return;
        }
        $http.patch(serviceFactory.settlementDetail(calcSettlementId) + 'advertising/', {
            advertising_fee_adjust: $scope.advertising_fee
        }).then(function (result) {
            $rootScope.addAlert('info', '设置成功');
            $scope.advertisingInvalid = false;
        }).catch(function (result) {
            $rootScope.addAlert('error', '发生异常');
        });
    }
});

app.controller('settlementDetailCtrl', function ($scope, $rootScope, $http, $stateParams, $uibModal, $timeout, serviceFactory, fileUpload) {
    $scope.settlementId = $stateParams.settlementId;
    var settlementId = $scope.settlementId;
    $scope.isSettlement = true;
    $scope.storage_uploading = false;   // 文件上传状态
    $scope.removal_uploading = false;   // 文件上传状态
    $scope.advertising_uploading = false;   // 文件上传状态
    $http.get(serviceFactory.settlementDetail(settlementId))
        .then(function (result) {
             $scope.settlement = result.data;
             // if (!$scope.settlement.subscribe_fee){
             //     openSetModal();
             // }
        });

    function openSetModal() {
        var modalInstance = $uibModal.open({
            templateUrl : 'templates/settlement/set_fee.html',//script标签中定义的id
            controller : 'setFeeCtrl',//modal对应的Controller
            resolve : {
                data : function() {//data作为modal的controller传入的参数
                    return $scope.settlement;//用于传递数据
                }
            }
        });
    }
    $scope.$on("subscribeFeeChange", function (event, msg) {
         $scope.settlement.subscribe_fee = msg;
     });
    $timeout(function () {
        angular.element("#storageFile").on('change', function(){
            $scope.storageFile = this.files[0];
        });
        angular.element("#removalFile").on('change', function(){
            $scope.fileToUpload = this.files[0];
        });
        angular.element("#advertisingFile").on('change', function(){
            $scope.advertisingFile = this.files[0];
        });
    }, 1000);
    $scope.sendRemovalFile = function(){
        var url = serviceFactory.uploadRemovals(settlementId),
            file = $scope.fileToUpload;
        if ( !file ) return;
        $scope.removal_uploading = true;
        fileUpload.uploadFileToUrl(file, url, function (data) {
            if (!data.errno){
                $rootScope.addAlert('success', '上传成功，一共找到' + data.data.length + '条记录');
                $scope.removals = data.data;
            }else {
                $rootScope.addAlert('error', '上传失败，请确认上传文件是否移除报告');
            }
        }, function(){
            $scope.removal_uploading = false;
        });
    };
    $scope.sendStorageFile = function(){
        var url = serviceFactory.settlementDetail(settlementId) + 'storage_upload/',
            file = $scope.storageFile;
        if ( !file ) return;
        $scope.storage_uploading = true;
        fileUpload.uploadFileToUrl(file, url, function (data) {
            if (!data.errno){
                $rootScope.addAlert('success', '上传成功，一共找到' + data.data.length + '条记录');
                $scope.removals = data.data;
            }else {
                $rootScope.addAlert('error', '上传失败，请确认上传文件是否移除报告');
            }
        }, function(){
            $scope.storage_uploading = false;
        });
    };
    $scope.sendAdvertisingFile = function() {   // 上传广告报告
        var url = serviceFactory.settlementDetail(settlementId) + 'advertising_upload/',
            file = $scope.advertisingFile;
        if ( !file ) return;
        $scope.advertising_uploading = true;
        fileUpload.uploadFileToUrl(file, url, function (data) {
            if (!data.errno){
                $rootScope.addAlert('success', '上传成功');
            }else {
                $rootScope.addAlert('error', '上传失败，请确认上传文件是否广告报告');
            }
        }, function(){
            $scope.advertising_uploading = false;
        });
    };

    $scope.setAdvertising = function () {
        if ($scope.advertising_fee == ''){
            return;
        }
        $http.patch(serviceFactory.settlementDetail(settlementId) + 'advertising/', {
            advertising_fee_adjust: $scope.advertising_fee
        }).then(function (result) {
            $rootScope.addAlert('info', '设置成功');
            $scope.advertisingInvalid = false;
        }).catch(function (result) {
            $rootScope.addAlert('error', '发生异常');
        });
    };

})
.controller('setFeeCtrl', function($scope, $rootScope, $http, $state, serviceFactory, $uibModalInstance, data) {
    $scope.settlement = data;
    //在这里处理要进行的操作
    $scope.save = function() {
        $http.patch(serviceFactory.settlementDetail($scope.settlement.id), {
            subscribe_fee: $scope.subscribe_fee
        }).then(function (result) {
            $uibModalInstance.close();
            $scope.$emit("subscribeFeeChange", $scope.subscribe_fee);
        }).catch(function (result) {
            $rootScope.addAlert('danger', '设置失败');
        });
    };
    $scope.cancel = function() {
        $uibModalInstance.close();
    }
});


app.controller('settlementOrdersCtrl', function ($scope, $rootScope, $http, $stateParams, $uibModal, serviceFactory, fileUpload, $timeout) {
    var settlementId = $stateParams.settlementId, productId = $stateParams.productId ? $stateParams.productId : '';
    $scope.settlementId = settlementId;
    $scope.isSettlement = productId ? false : true;
    $scope.fileToUpload = null;
    $scope.productSummary = {};
    $scope.products = [];
    $scope.orderSummary = {};
    $scope.orders = [];
    $scope.refundSummary = {};
    $scope.refunds = [];
    $scope.removalSummary = {};
    $scope.removals = [];
    $scope.lostSummary = {};
    $scope.losts = [];
    $scope.settlement = {};
    $scope.productLoading = true;
    $scope.orderLoading = true;
    $scope.refundLoading = true;
    $scope.removalLoading = true;
    $scope.lostLoading = true;
    var getTotalParam = {
        settlement: settlementId,
        product: productId,
        is_total: 1
    }, getListParam = {
        settlement: settlementId,
        is_total: 0
    };
    if (productId){
        getListParam['product'] = productId;
    }
    getOrders();
    getRefunds();
    getRemovals();
    getLosts();
    if ($scope.isSettlement)
    {
        getProducts();
    }

    function getProducts() {
        $http.get(serviceFactory.settlementProducts(settlementId))
            .then(function (result) {
                $scope.productLoading = false;
                $scope.products = result.data;
            }).catch(function (result) {
                $scope.productLoading = false;
                $rootScope.addAlert('warning', '获取商品列表失败');
            });
    }

    function getOrders() {
        $http.get(serviceFactory.settlementOrders(settlementId), {
            params: getListParam})
            .then(function (result) {
                $scope.orderLoading = false;
                $scope.orders = result.data;
            }).catch(function (result) {
                $scope.orderLoading = false;
                $rootScope.addAlert('warning', '获取商品列表失败');
            });
        $http.get(serviceFactory.settlementOrders(settlementId), {
            params: getTotalParam})
            .then(function (result) {
                if (result.data.length){
                    $scope.orderSummary = result.data[0];
                }
            }).catch(function (result) {
                $rootScope.addAlert('warning', '获取商品列表失败');
        });
    }
    function getRefunds() {
        $http.get(serviceFactory.settlementRefunds(settlementId), {
            params: getListParam})
            .then(function (result) {
                $scope.refundLoading = false;
                $scope.refunds = result.data;
            }).catch(function (result) {
            $scope.refundLoading = false;
            $rootScope.addAlert('warning', '获取商品列表失败');
        });
        $http.get(serviceFactory.settlementRefunds(settlementId), {
            params: getTotalParam})
            .then(function (result) {
                if (result.data.length);
                {
                    $scope.refundSummary = result.data[0];
                }
            }).catch(function (result) {
            $rootScope.addAlert('warning', '获取商品列表失败');
        });
    }
    function getRemovals() {
        $http.get(serviceFactory.settlementRemovals(settlementId), {
            params: getListParam})
            .then(function (result) {
                $scope.removalLoading = false;
                $scope.removals = result.data;
            }).catch(function (result) {
            $scope.removalLoading = false;
            $rootScope.addAlert('warning', '获取商品列表失败');
        });
        $http.get(serviceFactory.settlementRemovals(settlementId), {
            params: getTotalParam})
            .then(function (result) {
                if (result.data.length){
                    $scope.removalSummary =result.data[0];
                }
            }).catch(function (result) {
            $rootScope.addAlert('warning', '获取商品列表失败');
        });
    }
    function getLosts() {
        $http.get(serviceFactory.settlementLosts(settlementId), {
            params: getListParam})
            .then(function (result) {
                $scope.lostLoading = false;
                $scope.losts = result.data;
            }).catch(function (result) {
            $scope.lostLoading = false;
            $rootScope.addAlert('warning', '获取商品列表失败');
        });
        $http.get(serviceFactory.settlementLosts(settlementId), {
            params: getTotalParam})
            .then(function (result) {
                if (result.data.length){
                    $scope.lostSummary =result.data[0];
                }
            }).catch(function (result) {
            $rootScope.addAlert('warning', '获取商品列表失败');
        });
    }


    var selectedProducts = {};
    $scope.isCalcCost = false;
    $scope.isCalcProfit = false;
    $scope.selectProduct = function($event, index) {        // 选中/取消某个商品
        if ($event.target.checked)
        {
            selectedProducts[index] = $scope.products[index];
        }else {
            delete selectedProducts[index];
        }
    };

    $scope.calc_products = function(calc_type) {     // 计算选中的商品的成本
        var idList = [];
        for (var i in selectedProducts) {
            idList.push(selectedProducts[i].product.id);
        }
        if (!idList.length){
            return;
        }
        if (calc_type === 'calc_cost') {
            $scope.isCalcCost = true;
        } else {
            $scope.isCalcProfit = true;
        }
        $http.get(serviceFactory.getUrl('/api/settlements/' + settlementId + '/' + calc_type + '?products=' + idList.join(',')))
            .then(function (result) {
                if (result.data.errno) {
                    $rootScope.addAlert('error', '计算失败:' + result.data.message);
                } else {
                    $rootScope.addAlert('success', '计算完成');
                    for (var i in selectedProducts) {   // 取消已选
                        selectedProducts[i].selected = false;
                    }
                }
            }).catch(function (result) {
                $rootScope.addAlert('warning', '计算过程发生错误');
            }).finally(function(){
                $scope.isCalcCost = false;
                $scope.isCalcProfit = false;
            });
    };

    function openSetModal() {
        var modalInstance = $uibModal.open({
            templateUrl : 'templates/settlement/set_fee.html',//script标签中定义的id
            controller : 'setFeeCtrl',//modal对应的Controller
            resolve : {
                data : function() {//data作为modal的controller传入的参数
                    return $scope.settlement;//用于传递数据
                }
            }
        });
    }
    $scope.$on("subscribeFeeChange", function (event, msg) {
        $scope.settlement.subscribe_fee = msg;
    });
    // $("#removalFile").filestyle({buttonName: "btn-default", placeholder: "选择亚马逊下载的移除报告", buttonText: "浏览"});

    $scope.saveOrderCost = function (index, id){        // 修改某个订单的单位成本
        $http.patch(serviceFactory.orderDetail(id) + 'cost/', {
            cost: $scope.orders[index].cost
        }).then(function (result) {
            $rootScope.addAlert('info', '修改成功');
            $scope.orders[index] = result.data;
        }).catch(function (result) {
            $rootScope.addAlert('error', '修改失败');
        })
    };
    $scope.saveRefundCost = function (index, id){        // 修改refund的单位成本
        $http.patch(serviceFactory.refundDetail(id) + 'cost/', {
            cost: $scope.refunds[index].cost
        }).then(function (result) {
            $rootScope.addAlert('info', '修改成功');
            $scope.refunds[index] = result.data;
        }).catch(function (result) {
            $rootScope.addAlert('error', '修改失败');
        })
    };
    $scope.saveRemovalCost = function (index, id){        // 修改某个订单的单位成本
        $http.patch(serviceFactory.removalDetail(id) + 'cost/', {
            cost: $scope.removals[index].cost
        }).then(function (result) {
            $rootScope.addAlert('info', '修改成功');
            $scope.removals[index] = result.data;
        }).catch(function (result) {
            $rootScope.addAlert('error', '修改失败');
        })
    };
    $scope.saveLostCost = function (index, id){        // 修改某个订单的单位成本
        $http.patch(serviceFactory.lostDetail(id) + 'cost/', {
            cost: $scope.losts[index].cost
        }).then(function (result) {
            $rootScope.addAlert('info', '修改成功');
            $scope.losts[index] = result.data;
        }).catch(function (result) {
            $rootScope.addAlert('error', '修改失败');
        })
    };
});