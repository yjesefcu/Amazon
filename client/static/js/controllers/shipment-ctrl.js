"use strict";


app.directive('shipmentOrderRepeatDirective', function($timeout) {
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

app.controller('ShipmentCtrl', function ($scope, $http, $rootScope, $timeout, serviceFactory) {
    $scope.shipments = [];
    $http.get('/api/shipments', {
        params: {
            MarketplaceId: $rootScope.publicMarketplaceId
        }
    }).then(function (result) {
        sortOrders(result.data);
    }).catch(function (result) {

    });

    function sortOrders (orders) {     // 对移库单进行排列，将待办放前面
        var todos = [], others = [], userRole=$rootScope.userRole;
        orders.forEach(function (n) {
           if (n.status.role == userRole) {
                n.canEdit = true;
               todos.push(n);
           }  else {
               others.push(n);
           }
        });
        $scope.shipments = todos.concat(others);
    };

    $scope.deleteShipment = function(index, id){
        $http.delete(serviceFactory.shipmentDetail(id))
            .then(function (result) {
                $rootScope.addAlert('info', '删除成功');
                $scope.shipments.splice(index, 1);
            }).catch(function (result) {
                if (result.status === 400){
                    $rootScope.addAlert('error', '需删除所有商品记录后才能删除');
                    return;
                }
                $rootScope.addAlert('error', '修改失败');
            });
    };

    $scope.initDeleteConfirm = function () {
        $timeout(function () {

        $('#overseaTable .fa-trash-o').each(function (i, n) {
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
        $http.delete('/api/shipments/' + $scope.shipments[index].id).then(function (result) {
            $rootScope.addAlert('info', '删除成功');
            $scope.shipments.splice(index, 1);
        }).catch(function (result) {
            $rootScope.addAlert('error', '删除失败');
        })
    }
});

app.controller('OutboundEditCtrl', function ($scope, $http, $rootScope, $stateParams, $state, $timeout, $uibModal, serviceFactory) {
    var id = $stateParams.id;
    $scope.createBy = $stateParams.by;
    $scope.formData = {MarketplaceId: $rootScope.publicMarketplaceId};
    $scope.items = [];
    $scope.error_msg = '';
    $scope.volume_args_choice = [5000, 6000];
    $scope.boxs = [];
    $scope.canEdit = false;
    $scope.products = [];
    $scope.searchResults = [];
    $scope.searchResultsPosition = {};
    $scope.isSubmitting = false;

    if ($stateParams.products && $stateParams.products.length) {
        $stateParams.products.forEach(function (p) {
           $scope.items.push({SellerSKU: p.SellerSKU, product: p});
        });
    }

    $scope.addProductRow = function () {
        $scope.items.push({});
    };

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

    getProducts();

    $scope.chooseProduct = function (item, product) {

        item.SellerSKU = product.SellerSKU;
        item.product = product;
    };

    getShipment();

    function getShipment() {
        $http.get(serviceFactory.shipmentDetail(id)).then(function (result) {
            $scope.formData = result.data;
            $scope.items = result.data.items;
            if (result.data.status.id === 100 && $rootScope.userRole === result.data.status.role) {
                $scope.canEdit = true;
            } else {
                $scope.canEdit = false;
            }
        });
        $http.get('/api/shipments/' + id +'/boxs/').then(function (result) {
            $scope.boxs = result.data;
        });
    }
    $scope.save = function () {
        $scope.error_msg = '';
        var method, url;
        if (id){
            $scope.formData['id'] = id;
            method = 'patch';
            url = serviceFactory.shipmentDetail(id);
        }else{
            method = 'post';
            url = serviceFactory.outboundShipments();
        }
        $scope.formData['items'] = $scope.items;
        $scope.isSubmitting = true;
        $http({
            url: url,
            method: method,
            data: $scope.formData
        }).then(function (result) {
            console.log('create outbound shipment success');
            $scope.isSubmitting = false;
            $state.go('index.shipmentDetail', {id: result.data.id});
        }).catch(function (result) {
            console.log('create outbound shipment failed');
            $scope.isSubmitting = false;
            $rootScope.addAlert('danger', '保存失败');
            if (result.status == 400){
                $scope.error_msg = result.data.msg;
            }
        });
    };

    $scope.remove = function (index) {
        $scope.items.splice(index, 1);
    };

    $scope.saveItem = function (index, id) {    // 保存修改
        $scope.isSubmitting = true;
        $http.patch(serviceFactory.shipmentItemDetail(id), {unit_cost:$scope.items[index].unit_cost})
            .then(function (result) {
                $scope.isSubmitting = false;
                $rootScope.addAlert('info', '修改成功');
                $scope.items[index] = result.data;
                $scope.items[index].isEdit = false;
            }).catch(function (result) {
                $scope.isSubmitting = false;
                $rootScope.addAlert('error', '修改失败');
            });
    };

    $scope.deleteItem = function(index, id){    //删除子项
        $http.delete(serviceFactory.shipmentItemDetail(id))
            .then(function (result) {
                $rootScope.addAlert('info', '删除成功');
                $scope.items.splice(index, 1);
            }).catch(function (result) {
                if (result.status == 400){
                    $rootScope.addAlert('error', '库存 < 原始数量，无法删除');
                    return;
                }
                $rootScope.addAlert('error', '修改失败');
            });
    };

    var boxIndex = 0;
    $scope.addBox = function () {
        $scope.boxs.push({index: boxIndex});
        boxIndex += 1;
    };

    $scope.delBox = function (index) {
        for (var i=0; i<$scope.boxs.length; i++) {
            if ($scope.boxs[i].index == index) {
                var box = $scope.boxs[i];
                $scope.boxs.splice(i, 1);
                // 将已经填好的数量减去
                var boxProducts = box.products;
                if (boxProducts) {
                    $scope.items.forEach(function (p) {
                        if (boxProducts[p.id]) {
                            p.boxed_count -= parseInt(boxProducts[p.id]);
                        }
                    });
                }
                break;
            }
        }
    };

    $scope.boxCountInput = function (product) {
        var count = 0;
        $scope.boxs.forEach(function (box) {
            if (box.products && box.products[product.id])
            {
                count += parseInt(box.products[product.id]);
            }
        });
        product.boxed_count = count;
    };

    $scope.deleteShipment = function(){
        $http.delete(serviceFactory.shipmentDetail(id))
            .then(function (result) {
                $rootScope.addAlert('info', '删除成功');
                $timeout(function(){
                    window.history.back();
                }, 1000);
            }).catch(function (result) {
                if (result.status == 400){
                    $rootScope.addAlert('error', '需删除所有商品记录后才能删除');
                    return;
                }
                $rootScope.addAlert('error', '修改失败');
            });
    };

    $scope.getProductInfo = function(index){
        var product=$scope.items[index];
        if (!product['SellerSKU']){
            return;
        }
        $http.get(serviceFactory.getUrl('/product/sku/?SellerSKU='+product['SellerSKU'])).then(function(result){
            var returnData = result.data;
            product['name'] = returnData.TitleCn ? returnData.TitleCn : returnData.Title;
        }).catch(function(result){
            console.log('get product by sku fail');
        });
    };
    
    $scope.update = function () {   // 更新箱子信息
        var data = $.extend({}, $scope.formData, {'boxs': $scope.boxs});
        $http.patch('/api/shipments/' + id, data).then(function (result) {
            $rootScope.addAlert('success', '保存成功');
            getShipment(id);
        }).catch(function (exception) {
            $rootScope.addAlert('danger', '保存失败:' + exception.data)
        });
    };

    $scope.finish = function () {       // 关闭移库单
        $http.patch('/api/shipments/' + id + '/close').then(function (result) {
            getShipment(id);
        }).catch(function (exception) {
            console.log('error');
        });
    };

    $scope.sum = function (field, plusQuantity) {
        var total = 0;
       for (var i in $scope.items){
           if (plusQuantity){
               total += parseFloat($scope.items[i][field]) * $scope.items[i].QuantityShipped;
           }else{
               total += parseFloat($scope.items[i][field]);
           }
       }
        return total;
    };

    $scope.trackingTypeChange = function () {       // 切换海运/空运
        if ($scope.formData.traffic_fee || $scope.formData.tax_fee) {       // 重新计算所有商品的运费和关税

        }
        console.log($scope.formData.tracking_type);
    };


    $scope.openFeeInputModal = function () {        // 打开创建入库信息的对话框
        var modalInstance = $uibModal.open({
            templateUrl : '/static/templates/shipment/fee_input_modal.html',//script标签中定义的id
            controller : 'FeeInputModalCtrl',//modal对应的Controller
            resolve : {
                data : function() {//data作为modal的controller传入的参数
                    return {
                        order: $scope.formData
                    };//用于传递数据
                }
            }
        });
        modalInstance.result.then(function (result) {
            getShipment();
        });
    };

    // 重量或长度转换
    $scope.measureChange = function (box, key) {
        if (key === 'itn_weight') {
            box.weight = box.itn_weight ? (parseFloat(box.itn_weight) * 0.453) : 0;
        } else if (key === 'weight') {
            box.itn_weight = box.weight ? (parseFloat(box.weight) * 2.204) : 0;
        } else if (key.startsWith('itn_')) {
            box[key.substring(4)] = box[key] ? (parseFloat(box[key]) * 2.54) : 0;
        } else {
            box['itn_' + key] = box[key] ? (parseFloat(box[key]) * 0.394) : 0;
        }
    };

    $scope.downloadAsImage = function () {
        // html2canvas(document.body).then(function(canvas) {
        //      var imgUri = canvas.toDataURL("image/png", {}).replace("image/png", "image/octet-stream"); // 获取生成的图片的url
        //      window.location.href= imgUri; // 下载图片
        //  });
        html2canvas(document.getElementById('shipment_detail')).then(function (canvas) {
            var imgURL=canvas.toDataURL("image/png");
                $('#myIMG').attr("src",imgURL);
                // $('#b').on('click',function(){
                //     $('#down_qr').attr('download',imgURL);
                //     $('#down_qr').attr('href',imgURL);
                //     document.getElementById('down_qr').click();
                // });
            window.location.href = imgURL;
        });
    };
});

app.controller('ShipmentCreateCtrl', function ($scope, $http, $rootScope, $stateParams, $state, $timeout, serviceFactory) {
    $scope.id = $stateParams.id;
    $scope.formData = {MarketplaceId: $rootScope.publicMarketplaceId};
    $scope.items = [];
    $scope.error_msg = '';
    $scope.products = [];
    $scope.searchResults = [];
    $scope.searchResultsPosition = {};
    $scope.accounts = [];

    function formatAccount() {
        $http.get('/api/markets').then(function (response) {
            response.data.forEach(function (n, i) {
                n.account_name = n.country + '-' + n.account;
                $scope.accounts.push(n);
            });
        }).catch(function (exception) {
            $rootScope.addAlert('danger', '获取账户信息失败：' + exception.message);
        });
    }
    formatAccount();

    if ($stateParams.products && $stateParams.products.length) {
        $stateParams.products.forEach(function (p) {
           $scope.items.push({SellerSKU: p.SellerSKU, product: p});
        });
    }

    function getProducts () {
        $http.get("/api/products?MarketplaceId=public").then(function (result) {
            $scope.products = result.data;
        });
    }

    function getMarkets() {
    }
    getMarkets();

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

    getProducts();

    $scope.chooseProduct = function (item, product) {

        item.SellerSKU = product.SellerSKU;
        item.product = product;
    };

    if ($scope.id)
    {
        getShipment($scope.id);
    }

    function getShipment(id) {
        $http.get(serviceFactory.shipmentDetail(id)).then(function (result) {
            $scope.formData = result.data;
            $scope.items = result.data.items;
        });
    }

    $scope.addItem = function () {
        $scope.items.push({});
    };

    $scope.removeItem = function (index) {
        $scope.items.splice(index, 1);
    };

    $scope.save = function () {
        $scope.error_msg = '';
        var items = [];
        $scope.items.forEach(function (n) {
            if (n.SellerSKU && n.count) {
                items.push(n);
            }
        });
        if (!items.length) {
            return;
        }
        $scope.formData['items'] = items;
        $http({
            url: '/api/shipments/',
            method: 'post',
            data: $scope.formData
        }).then(function (result) {
            $rootScope.addAlert('success', '保存成功');
            $state.go('index.shipmentDetail', {id: result.data.id});
        }).catch(function (result) {
            console.log('create outbound shipment failed');
            $rootScope.addAlert('danger', '保存失败');
            if (result.status == 400){
                $scope.error_msg = result.data.msg;
            }
        });
    };

    $scope.delete = function () {       // 删除移库单
        $http.delete('/api/shipments/' + $scope.id).then(function (result) {
            // 跳回到列表页
            $rootScope.addAlert('success', '删除成功');
            $state.go('index.shipment');
        }).catch(function (exception) {
            $rootScope.addAlert('danger', '删除失败：' + exception.message);
        })
    };

});

app.controller('FeeInputModalCtrl', function ($scope, $http, $uibModalInstance, $rootScope, data) {
    $scope.order = data.order;
    $scope.error = '';
    $scope.isSubmitting = false;

    $scope.cancel = function() {
        $uibModalInstance.close();
    };

    $scope.submit = function () {       // 提交关闭采购单
        $scope.isSubmitting = true;
        $http.post('/api/shipments/' + $scope.order.id + '/payed/', {
            traffic_fee: $scope.traffic_fee,
            tax_fee: $scope.tax_fee
        }).then(function (result) {
            $scope.isSubmitting = false;
            $rootScope.addAlert('success', '提交成功');
            $uibModalInstance.close();
        }).catch(function (exception) {
            $scope.isSubmitting = false;
           $rootScope.addAlert("danger", '提交失败:' + exception.data);
        });
    }
});