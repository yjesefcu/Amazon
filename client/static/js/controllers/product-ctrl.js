"use strict";
/**
 * Created by liucaiyun on 2017/5/22.
 */
app.controller('ProductCtrl', function($scope, $http, $rootScope, $uibModal, $location, $state, serviceFactory) {
    $scope.products = [];
    $scope.selectedProducts = {};
    $http.get(serviceFactory.getAllProducts(), {
        params: {
            MarketplaceId: $rootScope.MarketplaceId,
            dataType: "json"
        }
    }).then(function (result) {
        $scope.products = result.data;
    }).catch(function (result) {
        $rootScope.addAlert('danger', '获取商品列表失败，status=' + result.status);
    });

    $scope.openSupplyModal = function (id) {
        var modalInstance = $uibModal.open({
            templateUrl : '/static/templates/product/add_supply.html',//script标签中定义的id
            controller : 'supplyModalCtrl',//modal对应的Controller
            resolve : {
                data : function() {//data作为modal的controller传入的参数
                    return {
                        id: id
                    };//用于传递数据
                }
            }
        });
    };

    $scope.cancelAllSelected = function () {
        $scope.products.forEach(function (n) {
           n.selected = false;
        });
    };

    $scope.createPurchasing = function () {
        var products = getProducts();
        $state.go('index.purchasingCreate', {id: '', products: products});
    };

    $scope.createShipment = function () {
        var products = getProducts();
        $state.go('index.createShipment', {id:'', products: products});
    };

    function getProducts() {
        var products = [];
        $scope.products.forEach(function (n) {
            if (n.selected) {
                products.push(n);
            }
        });
        return products;
    }
});

//模态框对应的Controller
app.controller('supplyModalCtrl', function($scope, $rootScope, $http, serviceFactory, $uibModalInstance, data) {
    $scope.productId = data.id;
    var callback = data.cb;
    $scope.supply = {product: data.id, MarketplaceId: $rootScope.MarketplaceId};
    //在这里处理要进行的操作
    $scope.save = function() {
        $scope.supply['inventory'] = $scope.supply['count'];       // 设置剩余数量与总数量一致

        $http.post(serviceFactory.supplyList($scope.productId), $scope.supply)
            .then(function (result) {
                $rootScope.addAlert('success', '添加入库信息成功');
                callback && callback(result.data);
                $uibModalInstance.close();
            }).catch(function (result) {
                if (result.status == 400){
                    var msg = [];
                    for (var key in result.data){
                        msg.push(key+"： " + result.data[key]);
                    }
                    $rootScope.addAlert('danger', '添加入库信息失败：'+ msg.join('; '));
                }
                else{
                    $rootScope.addAlert('danger', '添加入库信息失败，状态码：' + result.status);
                }
        });
    };
    $scope.cancel = function() {
        $uibModalInstance.close();
    };
});

app.directive('tableRepeatDirective', function($timeout) {
    return function(scope, element, attrs) {
        if (scope.$last){   // 表格repeat完毕
            $timeout(function(){
                if (angular.element(element.parent().parent())[0].nodeName == 'TABLE'){
                    angular.element(element.parent().parent())
                        .DataTable({
                        "paging": true,
                        "lengthChange": true,
                        "searching": true,
                        "ordering": false,
                        "info": true,
                        "autoWidth": false
                    });
                }
            }, 1000);
        }
    };
});

app.controller("ProductEditCtrl", function ($scope, $http, $rootScope, $location, $state, $timeout, $uibModal, $stateParams, serviceFactory, atomicNotifyService) {
    $scope.formData = {'MarketplaceId': $rootScope.MarketplaceId};
    $scope.productIcon = '';
    $scope.thumb = {};
    $scope.gifts = [];  // 赠品
    $scope.supplies = [];   // 入库货件
    $scope.shipments = [];  // 移库货件
    $scope.purchasingOrders = [];   // 采购单
    $scope.showSupplies = false;    // 是否显示入库货件列表
    $scope.showShipments = false;   // 是否显示移库货件列表
    $scope.purchasingOrders = false;    //是否显示采购单
    $scope.showSettlements = true;  // 是否显示结算列表
    $scope.productId = $stateParams.productId;
    var settlementId = $stateParams.settlementId;
    $scope.isDetail = $scope.productId ? true : false;
    if ($scope.productId){     // 编辑页面
        $http.get(serviceFactory.getProductDetail($scope.productId)).then(function (result) {
            $scope.formData = result.data;
            $scope.productIcon = serviceFactory.mediaPath(result.data.Image);
        });
        // getSupplies($scope.productId);
        // getShipments($scope.productId);
        getSettlements($scope.productId);
        // getPurchasingOrders($scope.productId);
    }
    // 获取赠品信息
    $http.get(serviceFactory.getProductDetail($scope.productId) + 'gifts/').then(function (response) {
        $scope.gifts = response.data;
    }).catch(function (exception) {
        $rootScope.addAlert('danger', '获取赠品信息失败');
    });
    $scope.submitForm = function () {
        var url = serviceFactory.createProduct(), method='post';
        if ($scope.productId){
            url = serviceFactory.getProductDetail($scope.productId);
            method = 'patch';
        }
        // 赠品信息
        var gifts = '';
        if ($scope.gifts.length) {
            $scope.gifts.forEach(function (n, i) {
               gifts += ',' + n.SellerSKU;
            });
            $scope.formData.gifts = gifts.substring(1);
        } else {
            $scope.formData.gifts = '';
        }
        $http({
            url: url,
            method: method,
            data: $scope.formData
        })
            .then(function (result) {
                if ($scope.productId){
                    $rootScope.addAlert('success', '保存成功', 3000);
                }else{
                    $rootScope.addAlert('success', '添加商品成功', 1000);
                }
                // 跳转到商品详情页
                $timeout(function () {
                    $state.go('index.productDetail', {productId: result.data.id});
                }, 500);
            }).catch(function (result) {
                if (result.status === 400){
                    var msg = [];
                    for (var key in result.data){
                        msg.push(key+"： " + result.data[key]);
                    }
                    $rootScope.addAlert('danger', '保存失败：'+ msg.join('; '));
                }
                else{
                    $rootScope.addAlert('danger', '保存失败，状态码：' + result.status);
                }
            });
    };

    $scope.img_upload = function(files) {       //单次提交图片的函数
        var data = new FormData(files[0]);      //以下为像后台提交图片数据
        data.append('image', files[0]);
        $http.post(
            serviceFactory.imageUpload(),
            data,
            {
                headers: {'Content-Type': undefined},
                transformRequest: angular.identity
            }
            ).then(function(result) {
                if (result.status == 200) {
                    $scope.productIcon = serviceFactory.mediaPath(result.data);
                    $scope.formData.Image = result.data;
                }
                else{
                    $rootScope.addAlert('danger', '上传图片失败');
                }
            }).catch(function (result) {
                if (result.status == 400){
                    var msg = [];
                    for (var key in result.data){
                        msg.push(key+"： " + result.data[key]);
                    }
                    $rootScope.addAlert('danger', '上传图片失败：'+ msg.join('; '));
                }
                else{
                    $rootScope.addAlert('danger', '上传图片失败，状态码：' + result.status);
                }
            });
    };
    $scope.settlements = [];
    function getSettlements(productId) {
        $http.get(serviceFactory.getSettlements(productId)).then(function (result) {
            $scope.selectedSettlement = result.data[0];
            $scope.settlements = result.data;
        });
    }

    function getSupplies(productId) {        // 获取入库货件
        $http.get(serviceFactory.getProductSupply(productId)).then(function (result) {
            $scope.supplies = result.data;
        });
    }

    function getShipments(productId) {  //获取移库货件
        $http.get(serviceFactory.getProductShipments(productId)).then(function (result) {
            $scope.shipments = result.data;
        });
    }

    function getPurchasingOrders(productId) {   // 获取采购单
        $http.get('/api/purchasing/?product_id=' + productId).then(function (result) {
            $scope.purchasingOrders = result.data;
        });
    }
    $scope.openSupplyModal = function (id) {
        var modalInstance = $uibModal.open({
            templateUrl : '/static/templates/product/add_supply.html',//script标签中定义的id
            controller : 'supplyModalCtrl',//modal对应的Controller
            resolve : {
                data : function() {//data作为modal的controller传入的参数
                    return {
                        id: id,
                        cb: function (data) {
                            $scope.supplies.push(data);
                        }
                    };//用于传递数据
                }
            }
        });
    };

    $scope.saveSupplyCost = function (index, id) {
        $http.patch(serviceFactory.supplyDetail(id), {
            unit_cost: $scope.supplies[index].unit_cost
        }).then(function (result) {
            $rootScope.addAlert('info', '保存成功');
            $scope.supplies[index] = result.data;
        }).catch(function (result) {
            $rootScope.addAlert('error', '保存失败');
        });
    };

    $scope.deleteSupply = function(index, id){
        $http.delete(serviceFactory.supplyDetail(id)).then(function (result) {
            $rootScope.addAlert('info', '删除成功');
            $scope.supplies.splice(index, 1);
        }).catch(function (result) {
            if (result.status === 400){
                $rootScope.addAlert('error', '库存 < 原始数量，无法删除');
                return;
            }
            $rootScope.addAlert('error', '保存失败');
        });
    };
    $scope.isCalculating = false;
    $scope.calc_products = function(settlementId) {     // 计算选中的商品的成本
        $scope.isCalculating = true;
        $http.get(serviceFactory.getUrl('/api/settlements/' + settlementId + '/calc_cost?products=' + $scope.productId))
            .then(function (result) {
                if (result.data.errno) {
                    $rootScope.addAlert('error', '计算失败:' + result.data.message);
                } else {
                    $rootScope.addAlert('success', '计算完成');

                }
            }).catch(function (result) {
                $rootScope.addAlert('warning', '计算过程发生错误');
            }).finally(function(){
                $scope.isCalculating = false;
            });
    };

    // 增加赠品
    $scope.addGift = function () {
        $scope.gifts.push({});
    };
    // 删除赠品
    $scope.deleteGift = function (sku) {
        for (var i=0; i<$scope.gifts.length; i++){
            if ($scope.gifts[i].SellerSKU == sku) {
                $scope.gifts.splice(i, 1);
                break;
            }
        }
    };


    if ($stateParams.products && $stateParams.products.length) {
        $stateParams.products.forEach(function (p) {
           $scope.items.push({SellerSKU: p.SellerSKU, product: p});
        });
    }
    // 商品搜索
    $scope.products = [];
    function getProducts () {
        $http.get("/api/products").then(function (result) {
            $scope.products = result.data;
        });
    }

    $scope.focusSearchInput = function ($event, sku) {
        var offset = $($event.target).offset();
        $scope.searchResultsPosition = {x: offset.left+'px', y: (offset.top+24)+'px'};
        $scope.skuSearch(sku);
    };

    $scope.skuSearch = function (sku) {     // 商品搜索
        if (!sku) {
            $scope.searchResults = $scope.products;
            return;
        }
        var results = [];
        sku = sku.toLowerCase();
        $scope.products.forEach(function (p) {
           if (p.SellerSKU.toLowerCase().indexOf(sku) >= 0) {
               results.push(p);
           }
        });
        $scope.searchResults = results;
    };

    $scope.chooseProduct = function (sku, product) {
        for (var i=0; i<$scope.gifts.length; i++){
            if ($scope.gifts[i].SellerSKU == sku) {
                $scope.gifts[i] = product;
                break;
            }
        }
    };

    getProducts();
    // 用于商品搜索
});

app.controller('ProductOrdersCtrl', function ($scope, $rootScope, $http, $location, $state, $stateParams, $timeout, serviceFactory) {
    var productId = $stateParams.productId, settlementId=$stateParams.settlementId;
    $scope.settlements = [];
    $scope.settlement = {};
    $http.get(serviceFactory.settlementDetail(settlementId))
        .then(function (result) {
            $scope.settlement = result.data;
        });
});
