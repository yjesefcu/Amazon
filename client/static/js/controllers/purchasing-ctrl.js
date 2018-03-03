/**
 * Created by liucaiyun on 2018/1/27.
 */
'use strict';


var OrderStatus = {
    'WaitForDepositPayed': 1,   //等待预付款付清
    'WaitForProducing':2,       // 等待采购员填写生产完成信息
    'WaitForPaying':3,          // 等待财务尾款打款
    'WaitForTraffic': 4,        // 等待采购员补充物流信息
    'WaitForInbound': 5,        // 等待仓库入库
    'WaitForCheck': 6,          // 等待采购员确认入库信息
    'WaitForTrafficFeePayed': 7,    // 等待物流费打款
    'FINISH': 8     // 完成
};

var Role = {
    'Finance': 'finance',
    'Purchasing': 'purchasing_agent',
    'CabManager': 'godown_manager',
    'Operator': 'operator'
};

app.controller('PurchasingOrderCreateCtrl', function ($scope, $http, $rootScope, $state, $stateParams) {
    $scope.order = {items: []};
    $scope.contract = {};
    $scope.searchResults = [];
    $scope.searchResultsPosition = {};

    if ($stateParams.products && $stateParams.products.length) {
        $stateParams.products.forEach(function (p) {
           $scope.order.items.push({SellerSKU: p.SellerSKU, product: p});
        });
    }

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

    $scope.chooseProduct = function (item, product) {

        item.SellerSKU = product.SellerSKU;
        item.product = product;
    };

    getProducts();

    $scope.addOrderItem = function () {
        $scope.order.items.push({});
    };

    $scope.save = function () {
        var items = [];
        $scope.order.items.forEach(function (n) {
           if (n.SellerSKU && n.count) {
               items.push(n);
           }
        });
        $scope.order.items = items;
        $http.post('/api/purchasing/', $scope.order).then(function (result) {
            $state.go('index.purchasingDetail', {orderId: result.data.id});
        }).catch(function (error) {
            $rootScope.addAlert('error', '创建采购单失败');
        });
    };

    $scope.remove = function (index) {
        $scope.order.items.splice(index, 1);
    };
});

app.controller('PurchasingOrderListCtrl', function ($scope, $http, $rootScope) {
    $scope.orders = [];

    function getData() {
        $http.get('/api/purchasing/').then(function (result) {
            $scope.orders = result.data;
            // 判断采购单是否可操作
            var userRole = $rootScope.userRole;
            $scope.orders.forEach(function (n) {
                if (n.status.role === userRole) {
                    n.canEdit = true;
                }
            });
        }).catch(function (error) {
             $rootScope.addAlert('error', '获取采购单失败');
        });
    }

    getData();
});

app.controller('PurchasingOrderDetailCtrl', function ($scope, $http, $rootScope, $stateParams, $uibModal) {
    $scope.orderId = $stateParams.orderId;
    $scope.order = {};
    $scope.product = {};
    $scope.inbounds = [];
    $scope.canCreate = false;

    function getData() {
        $http.get('/api/purchasing/' + $scope.orderId + '/').then(function (result) {
            $scope.order = result.data;
            $scope.product = result.data.product;
            var status_id = $scope.order.status.id;
            if ($rootScope.userRole === 'purchasing' && (status_id > 3 && status_id != 8))  // 只有财务才能添加物流
            {
                $scope.canCreate = true;
            }
        }).catch(function (error) {
            $rootScope.addAlert('error', '获取订单信息失败');
        });
    }

    $scope.update = function (params) {
        $http.patch('/api/purchasing/' + $scope.orderId + '/', params).then(function (result) {
            $rootScope.addAlert('info', '提交成功');
            $scope.refresh();
        }).catch(function (error) {
            $rootScope.addAlert('error', '提交失败');
        });
    };

    function init() {
        getData();
    }

    $scope.refresh = function () {
        init();
    };

    init();

    $scope.openPayModal = function () {        // 支付确认对话框
        var modalInstance = $uibModal.open({
            templateUrl : '/static/templates/purchasing/payment_modal.html',//script标签中定义的id
            controller : 'PurchasingOrderPaymentCtrl',//modal对应的Controller
            resolve : {
                data : function() {//data作为modal的controller传入的参数
                    return {
                        order: $scope.order
                    };//用于传递数据
                }
            }
        });
        modalInstance.result.then(function (result) {
            $scope.refresh();
        });
    };
});


// 订单付款对话框
app.controller('PurchasingOrderPaymentCtrl', function ($scope, $http, $uibModalInstance, $rootScope, data) {
    $scope.order = data.order;

    $scope.save = function () {
        $http.post('/api/purchasing/' + $scope.order.id + '/payed/', {
            fee: $scope.fee
        }).then(function (result) {
            $rootScope.addAlert('info', '提交成功');
            $uibModalInstance.close();
        }).catch(function (error) {
            $rootScope.addAlert('error', '提交失败');
        });
    };

    $scope.cancel = function() {
        $uibModalInstance.close();
    };
});

// 采购单的物流单
app.controller('PurchasingInboundsCtrl', function ($scope, $http, $uibModal) {

    $scope.orderId = $scope.$parent.orderId;

    function getInbounds () {
        var url = $scope.orderId ? '/api/purchasing/' + $scope.orderId + '/inbounds/' : '/api/inbounds'
        $http.get(url).then(function (result) {
            $scope.inbounds = result.data;
        }).catch(function (error) {

        });
    }

    function init() {
        getInbounds();
    }

    init();

    $scope.openInboudModal = function (id) {        // 打开创建入库信息的对话框
        var modalInstance = $uibModal.open({
            size: 'lg',
            templateUrl : '/static/templates/purchasing/create_inbound.html',//script标签中定义的id
            controller : 'PurchasingAddInboundCtrl',//modal对应的Controller
            resolve : {
                data : function() {//data作为modal的controller传入的参数
                    var items = [];
                    $scope.order.items.forEach(function (n) {
                        if (n.received_count < n.count)     // 只有数量未全部到货的商品才需要
                        {
                            items.push(n);
                        }
                    });
                    return {
                        id: id,
                        purchasingId: $scope.order.id,
                        items: items
                    };//用于传递数据
                }
            }
        });
        modalInstance.result.then(function (result) {
            getInbounds();
        });
    };

    $scope.openInputModal = function (inboundOrder) {        // 打开创建入库信息的对话框
        var modalInstance = $uibModal.open({
            size: 'lg',
            templateUrl : '/static/templates/purchasing/inbound_input.html',//script标签中定义的id
            controller : 'PurchasingInputCtrl',//modal对应的Controller
            resolve : {
                data : function() {//data作为modal的controller传入的参数

                    return {
                        order: inboundOrder
                    };//用于传递数据
                }
            }
        });
        modalInstance.result.then(function (result) {
            getInbounds();
        });
    };

    $scope.openPayModal = function (trafficOrder) {        // 物流费打款对话框
        var modalInstance = $uibModal.open({
            templateUrl : '/static/templates/purchasing/traffic_fee_confirm.html',//script标签中定义的id
            controller : 'InboundTrafficFeeConfirmCtrl',//modal对应的Controller
            resolve : {
                data : function() {//data作为modal的controller传入的参数
                    return {
                        order: trafficOrder
                    };//用于传递数据
                }
            }
        });
        modalInstance.result.then(function (result) {
            $scope.refresh();
        });
    };
});

app.controller('PurchasingAddInboundCtrl', function ($scope, $http, $rootScope, $state, data, $uibModalInstance) {
    var inboundId=data.id, purchasingId = data.purchasingId;
    $scope.items = data.items;
    $scope.order = {};
    $scope.error = '';

    $scope.inputChange = function () {
        $scope.error = '';
    };

    $scope.save = function () {
        var items = [];
        $scope.items.forEach(function (n) {
            if (n.expect_count) {
                items.push(n);
            }
        });
        if (!items.length) {
            $scope.error = '请至少填写一个商品的发货数量';
            return;
        }
        $scope.order.items = items;
        $http.post('/api/purchasing/' + purchasingId + '/inbounds/', $scope.order).then(function (result) {
            $rootScope.addAlert('info', '提交成功');
            $uibModalInstance.close();
            $state.go('index.purchasingDetail({orderId: orderId})');
        }).catch(function (error) {
            $rootScope.addAlert('error', '提交失败');
        });
    };

    var productChanged = false;
    $scope.productChanged = function () {
        productChanged = true;
    };

    $scope.cancel = function() {
        $uibModalInstance.close();
    };
});

// 物流入库对话框
app.controller('PurchasingInputCtrl', function ($scope, $http, $rootScope, $state, data, $uibModalInstance) {
    $scope.order = data.order;
    $scope.error = '';

    $scope.inputChange = function () {
        $scope.error = '';
    };

    function getData() {
        $http.get('/api/inbounds/'+$scope.order.id + '/').then(function (result) {
            $scope.order = result.data;
        });
    }

    getData();


    function checkFormValid() {     // 检查数据有效性
        var valid = true;
        $scope.order.items.forEach(function (n) {
           var p = n.product;
           if (!p.height || !p.weight || !p.length || !p.weight || !p.package_height || !p.package_width
               || !p.package_length || !p.package_weight || !n.received_count) {
               valid = false;
           }
        });
        return valid;
    }

    $scope.save = function () {
        if (!checkFormValid()) {
            $scope.error = '无法提交：请确认商品尺寸、到货数量等信息填写完整';
            return;
        }
        $http.post('/api/inbounds/' + $scope.order.id + '/putin/', $scope.order).then(function (result) {
            $rootScope.addAlert('info', '提交成功');
            $uibModalInstance.close();
            $state.go('index.purchasingDetail({orderId: orderId})');
        }).catch(function (error) {
            $rootScope.addAlert('error', '提交失败');
        });
    };

    $scope.cancel = function() {
        $uibModalInstance.close();
    };
});

app.controller('InboundTrafficFeeConfirmCtrl', function ($scope, $http, $uibModalInstance, $rootScope, data) {
    $scope.order = data.order;

    $scope.submit = function () {
        $http.post('/api/inbounds/' + $scope.order.id + '/payed/', {
            traffic_fee_payed: $scope.traffic_fee_payed
        }).then(function (result) {
            $rootScope.addAlert('info', '提交成功');
            $uibModalInstance.close();
        }).catch(function (error) {
            $rootScope.addAlert('error', '提交失败');
        });
    };

    $scope.cancel = function() {
        $uibModalInstance.close();
    };
});