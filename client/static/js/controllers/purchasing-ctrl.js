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

app.controller('PurchasingOrderCreateCtrl', function ($scope, $http, $rootScope, $state, $stateParams, $uibModal) {
    $scope.id = $stateParams.id;
    $scope.order = {items: []};
    $scope.contract = {};
    $scope.searchResults = [];
    $scope.searchResultsPosition = {};
    $scope.itemError = '';
    $scope.suppliers = [];
    if ($stateParams.products && $stateParams.products.length) {
        $stateParams.products.forEach(function (p) {
           $scope.order.items.push({SellerSKU: p.SellerSKU, product: p});
        });
    }

    function getSuppliers() {
        $http.get('/api/suppliers/').then(function (result) {
            $scope.suppliers = result.data;
        })
    }

    function getProducts () {
        $http.get("/api/products?MarketplaceId=" + $rootScope.publicMarketplaceId).then(function (result) {
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

    function init() {
        if ($scope.id) {
            $http.get('/api/purchasing/' + $scope.id + '/').then(function (result) {
                $scope.order = result.data;
            })
        }
        getProducts();
        getSuppliers();
    }

    init();

    $scope.addOrderItem = function () {
        $scope.order.items.push({});
        $scope.itemError = '';
    };

    $scope.delete = function (forward) {
        $http.delete('/api/purchasing/'+$scope.id+'/').then(function (result) {
            // 跳回到列表页
            if (forward)
            {
                $rootScope.addAlert('success', '删除成功');
                $state.go('index.purchasing');
            }
        }).catch(function (exception) {
            if (forward)
            {
                $rootScope.addAlert('danger', '删除失败:' + exception.data);
            }
        });
    };

    $scope.save = function () {
        if ($scope.orderForm.$invalid) {
            return;
        }
        var items = [];
        $scope.order.items.forEach(function (n) {
           if (n.SellerSKU && n.count) {
               items.push(n);
           }
        });
        if (!items.length) {
            $scope.itemError = '至少选择一个商品';
            return;
        }
        $scope.order.MarketplaceId = $rootScope.publicMarketplaceId;
        $scope.order.items = items;
        $http.post('/api/purchasing/', $scope.order).then(function (result) {
            $state.go('index.purchasingDetail', {orderId: result.data.id});
        }).catch(function (error) {
            $rootScope.addAlert('danger', '创建采购单失败');
        });
    };

    $scope.remove = function (index) {
        $scope.order.items.splice(index, 1);
    };

    $scope.addSupplier = function () {      // 添加供应商

        var modalInstance = $uibModal.open({
            size: 'lg',
            templateUrl: '/static/templates/purchasing/create_supplier.html',//script标签中定义的id
            controller: 'SupplierCreateCtrl',//modal对应的Controller
            resolve: {
                data: function () {//data作为modal的controller传入的参数
                    return {
                    };//用于传递数据
                }
            }
        });
        modalInstance.result.then(function (result) {
            if (result.newSupplier) {
                $scope.suppliers.push(result.newSupplier);
            }
        });
    }
});

// 添加供应商对话框
app.controller('SupplierCreateCtrl', function ($scope, data, $uibModalInstance) {

    $scope.save = function () {
        if ($scope.name)
        {
            $uibModalInstance.close({newSupplier: $scope.name});
        }
    };

    $scope.cancel = function() {
        $uibModalInstance.close();
    };
});


app.directive('purchasingOrderRepeatDirective', function($timeout) {
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
            scope.initDeleteConfirm();
        }
    };
});

app.controller('PurchasingOrderListCtrl', function ($scope, $http, $rootScope, $timeout) {
    $scope.orders = [];

    function getData() {
        $http.get('/api/purchasing/').then(function (result) {
            sortOrder(result.data);
        }).catch(function (error) {
             $rootScope.addAlert('error', '获取采购单失败');
        });
    }

    function sortOrder(orders) {        // 将待办的往前放
        var todos = [], others = [], userRole=$rootScope.userRole;
        orders.forEach(function (n) {
           if (n.status.role == userRole) {
                n.canEdit = true;
               todos.push(n);
           }  else {
               others.push(n);
           }
        });
        $scope.orders = todos.concat(others);
    }

    $scope.initDeleteConfirm = function () {
        $timeout(function () {

        $('#purchasingListTable .fa-trash-o').each(function (i, n) {
            $(this).confirmation({
                animation: true,
                placement: "bottom",
                title: "确定删除？",
                btnOkClass: 'text-red',
                href: 'javascript:void(0)',
                btnCancelClass: '',
                btnOkLabel: '是',
                btnCancelLabel: '否',
                onConfirm: function () {
                    var index = i;
                    deleteOrder(index);
                }
            });
        });
        }, 1000);
    };

    function deleteOrder(index) {
        $http.delete('/api/purchasing/' + $scope.orders[index].id).then(function (result) {
            $rootScope.addAlert('info', '删除成功');
            $scope.orders.splice(index, 1);
        }).catch(function (result) {
            $rootScope.addAlert('error', '删除失败');
        })
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
            var code = $scope.order.status.code;
            if ($rootScope.userRole === 'purchasing_agent' && (code === 'WaitForTraffic' || code === 'WaitForInbound' || code === 'TrafficConfirm') || code === 'WaitForCheck')  // 只有采购才能添加物流
            {
                $scope.canCreate = true;
            } else {
                $scope.canCreate = false;
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

    $scope.gotoNextStep = function (status_id) {     // 提交到下一步
        $http.patch('/api/purchasing/' + $scope.order.id + '/', {
            status_id: status_id
        }).then(function (result) {
            $rootScope.addAlert('success', '提交成功');
            init();
        }).catch(function (exception) {
            $rootScope.addAlert('error', '提交失败:' + exception.data);
        });
    };

    $scope.openInboudModal = function () {        // 打开创建入库信息的对话框
        var modalInstance = $uibModal.open({
            size: 'lg',
            templateUrl: '/static/templates/purchasing/create_inbound.html',//script标签中定义的id
            controller: 'PurchasingAddInboundModalCtrl',//modal对应的Controller
            resolve: {
                data: function () {//data作为modal的controller传入的参数
                    var items = [];
                    $scope.order.items.forEach(function (n) {
                        if (n.received_count < n.count)     // 只有数量未全部到货的商品才需要
                        {
                            items.push(n);
                        }
                    });
                    return {
                        purchasingId: $scope.order.id,
                        items: items
                    };//用于传递数据
                }
            }
        });
        modalInstance.result.then(function (result) {
            // getInbounds();
        });
    };

    $scope.toCloseOrder = function () {   // 关闭采购单
        var modalInstance = $uibModal.open({
            size: 'lg',
            templateUrl: '/static/templates/purchasing/order_submit_to_pay.html',//script标签中定义的id
            controller: 'PurchasingOrderSubmitToPayModalCtrl',//modal对应的Controller
            resolve: {
                data: function () {//data作为modal的controller传入的参数
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


    // 打开财务确认对话框
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

    $scope.clickEditOrderInfo = function () {       // 点击编辑基本信息
        var modalInstance = $uibModal.open({
            templateUrl : '/static/templates/purchasing/order_basic_info_editor.html',//script标签中定义的id
            controller : 'PurchasingOrderBasicInfoEditCtrl',//modal对应的Controller
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

// 订单基本信息修改
app.controller('PurchasingOrderBasicInfoEditCtrl', function ($scope, $http, $uibModalInstance, $rootScope, data) {
    $scope.order = $.extend({}, data.order);

    $scope.cancel = function() {
        $uibModalInstance.close();
    };

    $scope.save = function () {
        if ($scope.orderForm.$invalid) {
            return;
        }
        var postData = {
            contract_number: $scope.order.contract_number,
            operator: $scope.order.operator,
            expect_date: $scope.order.expect_date,
            supplier: $scope.order.supplier,
            contact_person: $scope.order.contact_person,
            contact_phone: $scope.order.contact_phone
        };
        $http.patch('/api/purchasing/' + $scope.order.id, postData).then(function (result) {
            $scope.cancel();
        }).catch(function (error) {
            $rootScope.addAlert('danger', '更新采购单失败');
        });
    };
});

// 订单付款对话框
app.controller('PurchasingOrderPaymentCtrl', function ($scope, $http, $uibModalInstance, $rootScope, data) {
    $scope.order = data.order;

    $scope.submit = function () {
        // $http.post('/api/purchasing/' + $scope.order.id + '/payed/', {
        //     deposit_payed: $scope.deposit_payed,
        //     final_payment_payed: $scope.final_payment_payed,
        //     traffic_fee_payed: $scope.traffic_fee_payed
        // }).then(function (result) {
        //     $rootScope.addAlert('info', '提交成功');
        //     $uibModalInstance.close();
        // }).catch(function (error) {
        //     $rootScope.addAlert('error', '提交失败');
        // });
        $http.patch('/api/purchasing/' + $scope.order.id + '/', {        // 关闭采购单
            status_id: 10
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

    // 驳回至采购员
    $scope.reject = function () {

        $http.patch('/api/purchasing/' + $scope.order.id + '/',
            {status_id: 11}
        ).then(function (result) {
            // $rootScope.addAlert('success', '关闭成功');
            $uibModalInstance.close();
        }).catch(function (exception) {
           $rootScope.addAlert("danger", '提交失败:' + exception.data);
        });
    };
});

// 物流记录表格repeat
app.directive('purchasingInboundsRepeatDirective', function($timeout) {
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
            scope.initDeleteConfirm();
        }
    };
});

// 采购单的物流单
app.controller('PurchasingInboundsCtrl', function ($scope, $http, $uibModal, $timeout, $rootScope) {

    $scope.orderId = $scope.$parent.orderId;

    function getInbounds () {
        var url = $scope.orderId ? '/api/purchasing/' + $scope.orderId + '/inbounds/' : '/api/inbounds';
        $http.get(url).then(function (result) {
            $scope.inbounds = result.data;
        }).catch(function (error) {

        });
    }

    function init() {
        getInbounds();
    }

    init();

    $scope.openInputModal = function (inboundOrder) {        // 打开创建入库信息的对话框
        var modalInstance = $uibModal.open({
            size: 'lg',
            templateUrl : '/static/templates/purchasing/inbound_input.html',//script标签中定义的id
            controller : 'PurchasingInputModalCtrl',//modal对应的Controller
            resolve : {
                data : function() {     //data作为modal的controller传入的参数

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

    $scope.openInboundDetailModal = function ($event, inboundOrder) {        // 打开物流单详情
        if ($event.target.tagName === 'A') {
            return;
        }
        var modalInstance = $uibModal.open({
            size: 'lg',
            templateUrl : '/static/templates/purchasing/inboud-detail.html',//script标签中定义的id
            controller : 'PurchasingInputDetailModalCtrl',//modal对应的Controller
            resolve : {
                data : function() {     //data作为modal的controller传入的参数
                    return {
                        order: inboundOrder
                    };//用于传递数据
                }
            }
        });
    };

    $scope.openPayModal = function (trafficOrder) {        // 物流费打款对话框
        var modalInstance = $uibModal.open({
            templateUrl : '/static/templates/purchasing/traffic_fee_confirm.html',//script标签中定义的id
            controller : 'InboundTrafficFeeConfirmModalCtrl',//modal对应的Controller
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

    $scope.openConfirmModal = function (trafficOrder) {     // 确认到货对话框
        var modalInstance = $uibModal.open({
            templateUrl : '/static/templates/purchasing/traffic_confirm_modal.html',//script标签中定义的id
            controller : 'InboundReceiveConfirmCtrl',//modal对应的Controller
            resolve : {
                data : function() {//data作为modal的controller传入的参数
                    return {
                        order: trafficOrder
                    };//用于传递数据
                }
            }
        });
        modalInstance.result.then(function (result) {
            getInbounds();
        });
    };

    // 删除confirm
    $scope.initDeleteConfirm = function () {
        $timeout(function () {

        $('#inbounds_table .fa-trash-o').each(function (i, n) {
            $(this).confirmation({
                animation: true,
                placement: "bottom",
                title: "确定删除？",
                btnOkClass: 'text-red',
                href: 'javascript:void(0)',
                btnCancelClass: '',
                btnOkLabel: '是',
                btnCancelLabel: '否',
                onConfirm: function () {
                    var index = i;
                    deleteInbound(index);
                }
            });

        });
        }, 1000);
    };

    function deleteInbound(index) {  // 删除发货记录
        $http.delete('/api/purchasing/' + $scope.orderId + '/inbounds/' + $scope.inbounds[index].id).then(function (response) {
            $rootScope.addAlert("info", '删除成功');
            $scope.inbounds.splice(index, 1);
            location.reload();      // 刷新页面
        }).catch(function (response) {
            $rootScope.addAlert("danger", '删除失败');
        });
    }
});

app.controller('PurchasingAddInboundModalCtrl', function ($scope, $http, $rootScope, $state, data, $uibModalInstance) {
    var inboundId=data.id, purchasingId = data.purchasingId;
    $scope.items = data.items;
    $scope.order = {};
    $scope.error = '';

    $scope.items.forEach(function (n) {
        n.remain_count = n.count - (n.expect_count ? n.expect_count : 0);
        n.expect_count = 0;
    });

    $scope.inputChange = function () {
        $scope.error = '';
    };

    $scope.save = function () {
        var items = [];
        $scope.items.forEach(function (n) {
            if (n.expect_count && parseInt(n.expect_count) > 0) {
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
            location.reload();
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

    // 点击修改单价
    $scope.changePrice = function (item) {
        item.isEdit = true;
        item.newPrice = item.price;
    };

    // 修改商品单价
    $scope.savePrice = function (item) {
        item.price = item.newPrice;
        item.isEdit = false;
    };
});

app.controller('PurchasingInputDetailModalCtrl', function ($scope, $http, $rootScope, $state, data, $uibModalInstance) {
    $scope.order = data.order;

    // function getData() {
    //     $http.get('/api/inbounds/'+$scope.order.id + '/').then(function (result) {
    //         $scope.order = result.data;
    //     });
    // }
    //
    // getData();

    $scope.cancel = function() {
        $uibModalInstance.close();
    };
});

// 物流入库对话框
app.controller('PurchasingInputModalCtrl', function ($scope, $http, $rootScope, $state, data, $uibModalInstance) {
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
        if (!$scope.order.traffic_fee) {
            $scope.error = '无法提交：运费不能为空';
            return false;
        }
        var valid = true;
        $scope.order.items.forEach(function (n) {
           var p = n.product;
           if (!p.height || !p.weight || !p.length || !p.weight || !p.package_height || !p.package_width
               || !p.package_length || !p.package_weight || !n.received_count) {
                $scope.error = '无法提交：请确认商品尺寸、到货数量等信息填写完整';
               valid = false;
           }
        });
        return valid;
    }

    $scope.save = function () {
        if (!checkFormValid()) {
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

app.controller('InboundTrafficFeeConfirmModalCtrl', function ($scope, $http, $uibModalInstance, $rootScope, data) {
    $scope.order = data.order;

    $scope.submit = function () {
        $http.post('/api/inbounds/' + $scope.order.id + '/payed/', {
            traffic_fee_payed: $scope.traffic_fee_payed,
            payment_comment: $scope.payment_comment
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

app.controller('PurchasingOrderSubmitToPayModalCtrl', function ($scope, $http, $uibModalInstance, $rootScope, data) {
    $scope.order = data.order;
    $scope.error = '';

    if ($scope.order.count !== $scope.order.received_count) {
        $scope.error = '已到货数量与采购数量不符，确认要提交财务吗？'
    }

    $scope.cancel = function() {
        $uibModalInstance.close();
    };

    $scope.submit = function () {       // 提交关闭采购单
        $http.patch('/api/purchasing/' + $scope.order.id + '/',
            {status_id: 9,
            items: $scope.order.items}
        ).then(function (result) {
            // $rootScope.addAlert('success', '关闭成功');
            $uibModalInstance.close();
        }).catch(function (exception) {
           $rootScope.addAlert("danger", '提交失败:' + exception.data);
        });
    };

    $scope.changeTotalFee = function (productOrder) {
        productOrder.isEdit = true;
        productOrder.newTotalFee = productOrder.total_fee;
    };

    $scope.saveTotalFeeChange = function (productOrder) {
        productOrder.isEdit = false;
        productOrder.total_fee = productOrder.newTotalFee;
    }
});


app.controller('InboundReceiveConfirmCtrl', function ($scope, $http, $uibModalInstance, $rootScope, data) {
    $scope.order = data.order;
    $scope.error = '';

    $scope.cancel = function() {
        $uibModalInstance.close();
    };

    $scope.submit = function () {       // 提交关闭采购单
        $http.post('/api/inbounds/' + $scope.order.id + '/received/').then(function (result) {
            // $rootScope.addAlert('success', '关闭成功');
            $uibModalInstance.close();
        }).catch(function (exception) {
           $rootScope.addAlert("danger", '关闭失败:' + exception.data);
        });
    }
});