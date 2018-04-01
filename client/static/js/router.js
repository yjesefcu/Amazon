"use strict";

app.config(['$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider) {
    $urlRouterProvider.otherwise('/products');

    $stateProvider
        .state('index', {
            url:'/'
        })
        .state('index.users', {
            url:'users',
            templateUrl: '/static/templates/users/users.html',
            controller: 'UserCtrl'
        })
        .state('index.products', {
            url:'products',
            templateUrl: '/static/templates/product/products.html'
            // controller: 'ProductCtrl'
        })
        .state('index.productEdit', {
            url: 'products/create',
            templateUrl: '/static/templates/product/product_edit.html'
        })
        .state('index.productDetail', {
            url: 'product/:productId',
            templateUrl: '/static/templates/product/product_detail.html'
        })
        .state('index.productDetailEdit', {
            url: 'product/:productId/edit',
            templateUrl: '/static/templates/product/product_edit.html'
        })
        .state('index.productDetail.settlement', {
            url: '/settlement/:settlementId',
            templateUrl: '/static/templates/product/product_orders.html'
        })
        .state('index.productDetail.settlement.orders', {
            url: '/orders',
            templateUrl: '/static/templates/settlement_order_detail.html',
            controller: 'settlementOrdersCtrl'
        })
        .state('index.shipment', {
            url: 'shipment',
            templateUrl: '/static/templates/shipment/shipments.html'
        })
        .state('index.addSupply', {
            url: 'supply/create',
            templateUrl: '/static/templates/shipment/supply-create.html'
        })
        .state('index.createShipment', {
            url: 'shipment/create/:id',
            templateUrl: '/static/templates/shipment/shipment_create.html',
            params: {
                products: []
            }
        })
        .state('index.createShipOversea', {
            url: 'shipment/create/:by',
            templateUrl: '/static/templates/shipment/shipment_create.html'
        })
        .state('index.shipmentDetail', {
            url: 'shipment/:id',
            templateUrl: '/static/templates/shipment/shipment_detail.html',
            controller: 'OutboundEditCtrl'
        })
        .state('index.settlement', {
            url: 'settlement',
            templateUrl: '/static/templates/settlement/settlements.html'
        })
        .state('index.settlement.detail', {
            url: '/:settlementId',
            templateUrl: '/static/templates/settlement/settlement_detail.html'
        })
        .state('index.settlement.detail.orders', {
            url: '/orders',
            templateUrl: '/static/templates/settlement_order_detail.html',
            controller: 'settlementOrdersCtrl'
        })
        .state('index.purchasing', {
            url:'purchasing',
            templateUrl: '/static/templates/purchasing/purchasing-list.html'
            // controller: 'ProductCtrl'
        })
        .state('index.purchasingCreate', {
            url: 'purchasing/create/:id',
            templateUrl: 'static/templates/purchasing/order_create.html',
            params: {
                products: []
            }
        })
        .state('index.purchasingDetail', {
            url: 'purchasing/:orderId',
            templateUrl: 'static/templates/purchasing/purchasing-detail.html'
        })
        .state('index.purchasingDetail.inboundCreate', {
            url: '/addInbound',
            templateUrl: 'static/templates/purchasing/create_inbound.html'
        })
        .state('index.gifts', {
            url: 'gifts',
            templateUrl: 'static/templates/gift/gift-list.html'
        })
        .state('index.giftsCreate', {
            url: 'gifts/create',
            templateUrl: 'static/templates/gift/gift-create.html'
        })
    ;
}]);