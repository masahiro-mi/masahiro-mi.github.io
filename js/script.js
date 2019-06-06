/* ===================================================================

 * ヘッダの余白設定

=================================================================== */
$(function() {
	var headerMarginTop = parseInt($('header').css('margin-top'), 10);
	var navHeight = $('nav').outerHeight(true);
	$('header').css({'margin-top':navHeight + headerMarginTop});
});
