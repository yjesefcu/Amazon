"use strict";

app.controller('ShipmentCtrl', function ($scope, $http, $rootScope, serviceFactory) {
    $scope.shipments = [];
    $http.get('/api/shipments', {
        params: {
            MarketplaceId: $rootScope.MarketplaceId
        }
    }).then(function (result) {
        $scope.shipments = result.data;
    }).catch(function (result) {

    });

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
    }
});

app.controller('OutboundEditCtrl', function ($scope, $http, $rootScope, $stateParams, $state, $timeout, serviceFactory) {
    var id = $stateParams.id;
    $scope.createBy = $stateParams.by;
    $scope.formData = {MarketplaceId: $rootScope.MarketplaceId};
    $scope.items = [];
    $scope.error_msg = '';
    $scope.volume_args_choice = [5000, 6000];
    $scope.boxs = [];
    $scope.editDisable = false;
    $scope.products = [];
    $scope.searchResults = [];
    $scope.searchResultsPosition = {};

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

    $scope.isDetail = id ? true : false;
    if ($scope.isDetail)
    {
        getShipment(id);
    }

    function getShipment(id) {
        $http.get(serviceFactory.shipmentDetail(id)).then(function (result) {
            $scope.formData = result.data;
            $scope.items = result.data.items;
            if (result.data.status.id === 102 || $rootScope.userRole !== result.data.status.role) {
                $scope.editDisable = true;
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
        $http({
            url: url,
            method: method,
            data: $scope.formData
        }).then(function (result) {
            console.log('create outbound shipment success');
            $state.go('index.shipmentDetail', {id: result.data.id});
        }).catch(function (result) {
            console.log('create outbound shipment failed');
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
        $http.patch(serviceFactory.shipmentItemDetail(id), {unit_cost:$scope.items[index].unit_cost})
            .then(function (result) {
                $rootScope.addAlert('info', '修改成功');
                $scope.items[index] = result.data;
                $scope.items[index].isEdit = false;
            }).catch(function (result) {
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

    $scope.addBox = function () {
        $scope.boxs.push({});
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
            getShipment(id);
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


    $scope.calc = function(){       // 计算每个商品的运费和关税
        var p, totalWeight=0, totalPrice= 0, totalFreight= 0,totalTax=0;
        for (var i in $scope.products){
            p = $scope.products[i];
            if ($scope.createBy == 'sea')
            {
                p.volume_weight = p.width * p.height * p.length / $scope.volume_args;
                p.unit_weight = Math.max(parseFloat(p.volume_weight), parseFloat(p.weight));
            }else{
                p.unit_weight = p.width * p.length * p.height / 1000000;
            }
            totalWeight += p.unit_weight * p.QuantityShipped;
            totalPrice += p.unit_price * p.QuantityShipped;
        }
        // 计算每个商品的运费和关税
        for (var i in $scope.products){
            p = $scope.products[i];
            p.total_freight = p.unit_weight * p.QuantityShipped  / totalWeight * $scope.formData.total_freight;
            totalFreight += p.total_freight;
            p.duty = p.unit_price* p.QuantityShipped  / totalPrice * $scope.formData.duty;
            totalTax += p.duty;
        }
        $scope.totalWeight = totalWeight;
        $scope.totalTax = totalTax;
        $scope.totalFreight = totalFreight;
    };

    $scope.totalWeight = 0;
    $scope.totalTax = 0;
    $scope.totalFreight = 0;

    $scope.calc = function(){
        var p, totalWeight=0, totalPrice= 0, totalFreight= 0,totalTax=0;
        for (var i in $scope.items){
            p = $scope.items[i];
            if ($scope.createBy == 'sea')
            {
                p.volume_weight = p.width * p.height * p.length / $scope.volume_args;
                p.unit_weight = Math.max(parseFloat(p.volume_weight), parseFloat(p.weight));
            }else{
                p.unit_weight = p.width * p.length * p.height / 1000000;
            }
            totalWeight += p.unit_weight * p.QuantityShipped;
            totalPrice += p.unit_price * p.QuantityShipped;
        }
        // 计算每个商品的运费和关税
        for (var i in $scope.items){
            p = $scope.items[i];
            p.total_freight = p.unit_weight * p.QuantityShipped  / totalWeight * $scope.formData.total_freight;
            totalFreight += p.total_freight;
            p.duty = p.unit_price* p.QuantityShipped  / totalPrice * $scope.formData.duty;
            totalTax += p.duty;
        }
        $scope.totalWeight = totalWeight;
        $scope.totalTax = totalTax;
        $scope.totalFreight = totalFreight;
    };

    $scope.avgTax = function(){


        for (var i in $scope.items){

        }
    }
});