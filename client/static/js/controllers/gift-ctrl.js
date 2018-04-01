/**
 * Created by luohusi on 2018/4/1.
 */
app.controller('GiftPackingListCtrl', function ($scope, $http, $rootScope) {
     $http.get('/api/gifts/packing/').then(function (response) {
         $scope.records = response.data;
     }).catch(function (exception) {
         $rootScope.addAlert('danger', '获取打包记录失败');
     });
});

app.controller('GiftPackingCreateCtrl', function ($scope, $http, $rootScope, $state) {
    $scope.items = [];

    function getProducts () {
        $http.get("/api/products/gifts").then(function (result) {
            $scope.products = result.data;
        });
    }

    getProducts();

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


    $scope.addItem = function () {
        $scope.items.push({});
    };

    $scope.delItem = function (sku) {
        for (var i=0; i<$scope.items.length; i++){
            if ($scope.items[i].SellerSKU == sku) {
                $scope.items.splice(i, 1);
                break;
            }
        }
    };
    
    $scope.save = function () {
        var items = [];
        $scope.items.forEach(function (n) {
           if (n.SellerSKU && n.count) {
               items.push(n);
           }
        });
        if (!items.length){
            return;
        }
        $http.post('/api/gifts/packing/', {
            items: items
        }).then(function (response) {
            $state.go('index.gifts');
        }).catch(function (exception) {
            $rootScope.addAlert('danger', '保存失败');
        })
    };

});