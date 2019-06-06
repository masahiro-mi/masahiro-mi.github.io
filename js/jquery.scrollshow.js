/* =========================================================*/
// jquery.scrollshow.js / ver.1.1

// Copyright (c) 2014 CoolWebWindow
// This code is released under the MIT License
// http://www.coolwebwindow.com/jquery-plugin/rules/

// Date: 2015-12-28
// Author: CoolWebWindow
// Mail: info@coolwebwindow.com
// Web: http://www.coolwebwindow.com

// Used jquery.js
// http://jquery.com/
/* =========================================================*/

$(function($){
    $.fn.scrollshow = function(config) {
        // オプション
        var o = $.extend({
            position : 400 // 表示位置
        }, config);

        var $element = $(this);

        // 要素の非表示
        if ($(window).scrollTop() < o.position){
            $element.hide();
        }
        // スクロールすると表示させる
        $(window).scroll(function(){
            if ($(this).scrollTop() >= o.position) {
                $element.not(':animated').fadeIn();
            } else {
                $element.not(':animated').fadeOut();
            }
        });
    };
});
