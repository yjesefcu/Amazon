"use strict";

app.factory('serviceFactory', function ($rootScope) {
    var host='', services = {};
    $rootScope.host = host;
    services.markets = function () {
        return host + '/api/markets/';
    };
    services.getSettlements = function (productId) {
        if (productId){
            return host + '/api/products/' + productId + '/settlements/';
        }
        return host + '/api/settlements/';
    };
    services.createProduct = function () {
        return host + '/api/products/';
    };
    services.getAllProducts = function () {
        return host + '/api/products/';
    };
    services.getProductDetail = function (id) {
        return host + '/api/products/' + id + '/';
    };
    services.getProductSupply = function (productId) {
        return host + '/api/products/' + productId + '/supply/';
    };
    services.supplyDetail = function (supplyId) {
        return host + '/api/supply/' + supplyId + '/';
    };
    services.getProductShipments = function (productId) {
        return host + '/api/products/' + productId + '/shipments/';
    };
    services.getProductOrders = function (id) {
        return host + '/api/products/' + id + '/orders';
    };
    services.getProductRefunds = function (id) {
        return host + '/api/products/' + id + '/refunds';
    };
    services.getProductLosts = function (id) {
        return host + '/api/products/' + id + '/losts';
    };
    services.getProductRemovals = function (id) {
        return host + '/api/products/' + id + '/removals';
    };
    services.supplyList = function (productId) {
        return host + '/api/products/' + productId + '/supply/';
    };
    services.outboundShipments = function () {
        return host + '/api/shipments/';
    };
    services.shipmentDetail = function (id) {
        return host + '/api/shipments/' + id + '/';
    };
    services.shipmentItemDetail = function (id) {
        return host + '/api/shipmentItems/' + id + '/';
    };
    services.settlements = function () {
        return host + '/api/settlements/';
    };
    services.settlementDetail = function (id) {
        return host + '/api/settlements/' + id + '/';
    };
    services.settlementProducts = function (settlementId) {
        return host + '/api/settlements/' + settlementId + '/products/';
    };
    services.getUrl = function(url){
        return host + url;
    };
    services.settlementOrders = function (settlementId) {
        return host + '/api/settlements/' + settlementId + '/orders/';
    };
    services.settlementRefunds = function (settlementId) {
        return host + '/api/settlements/' + settlementId + '/refunds/';
    };
    services.settlementRemovals = function (settlementId) {
        return host + '/api/settlements/' + settlementId + '/removals/';
    };
    services.settlementLosts = function (settlementId) {
        return host + '/api/settlements/' + settlementId + '/losts/';
    };
    services.settlement = function (settlementId) {
        return host + '/api/settlements/' + settlementId + '/orders/';
    };
    services.imageUpload = function () {
        return host + '/image/upload/';
    };
    services.mediaPath = function (imagePath) {
        return host + imagePath;
    };
    services.uploadRemovals = function (settlementId) {
        return host + '/api/settlements/' + settlementId + '/removals/upload/';
    };
    services.downloadPath = function (path) {
        return host + path;
    };

    services.orderDetail = function (id) {
        return host + '/api/orders/' + id + '/';
    };
    services.refundDetail = function (id) {
        return host + '/api/refunds/' + id + '/';
    };
    services.removalDetail = function (id) {
        return host + '/api/removals/' + id+'/';
    };
    services.lostDetail = function (id) {
        return host + '/api/losts/' + id + '/';
    };
    return services;
});