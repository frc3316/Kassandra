'use strict';

/* Controllers */

var Kassandra = angular.module('Kassandra', []);

Kassandra.controller('defenceListCtrl', function($scope) {
  $scope.defences = [
	{name:"Portcullis", type:"a1", successfuls:14, attempted:32, size:1, color:"warning"},
	{name:"Moat", type:"b2", successfuls:8, attempted:26, size:2, color:"success"},
	{name:"Sally Port", type:"c2", successfuls:6, attempted:26, size:2, color:"info"},
	{name:"Ramparts", type:"b1", successfuls:2, attempted:15, size:3, color:"success"},
	];
});

