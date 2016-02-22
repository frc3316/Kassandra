'use strict';

/* Controllers */

var Kassandra = angular.module('Kassandra', []);

Kassandra.controller('defenceListCtrl', function($scope) {
  $scope.breaching = [
	{name:"Portcullis", type:"a1solo", successful:14, attempted:32, size:4, color:"danger", teams: [1,2,3]},
	{name:"Moat", type:"b2", successful:8, attempted:26, size:5, color:"success", teams: []},
	{name:"Sally Port", type:"c2assist", successful:6, attempted:26, size:5, color:"warning", teams: [1,2,3]},
	{name:"Ramparts", type:"b1", successful:2, attempted:15, size:6, color:"success", teams: [1,2,3]},
	{name:"Rock Wall", type:"d2", successful:2, attempted:11, size:6, color:"success", teams: [1,2,3]},
	];

 $scope.shooting = {
 	high: {
 		far:   {successful:6, attempted:7, size:4, color: "success", teams: [1,2,3], variant: true},
 		close: {successful:0, attempted:0.7, size:6, color: "danger", teams: [], variant: false}
 	},
 	low : {
 		far:   {successful:0, attempted:0, size:6, color: "danger", teams: [1,2,3], variant: false},
 		close: {successful:2, attempted:4, size:5, color: "warning", teams: [], variant: false}
 	}
 };

 $scope.collection = {floor: {color: "success", amount: 5, size:5, teams: [1,2,3]},
                      hp: {color: "warning", amount: 1, size: 5, teams: [1,2,3]}};

 $scope.end_game = {scale:     {color: "success", percentage: '47.0%', size: 4, teams: [1,2]},
                    challenge: {color: "warning", percentage: '10.33%', size: 6, teams: [3]}};

 $scope.defences = [
 	{tactic: "Pinning", team: 2315, match: 'Q1'},
 	{tactic: "T-Boning", team: 245, match: 'Q7'},
 	{tactic: "Pinning", team: 1242, match: 'SF-1 1'},
 ];
});

