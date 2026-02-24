/**
 * Fixes header alignment for left-scrollbar DataTables.
 * Detects scrollbar width and adjusts the header to match the body offset.
 *
 * On platforms with overlay scrollbars (Mac), scrollbar width is 0 and no
 * header adjustment is needed — DataTables handles alignment natively.
 * On platforms with classic scrollbars (Windows/Linux), the header must be
 * offset by the scrollbar width since direction:rtl moves it to the left.
 */
(function() {
    var scrollbarWidth = null; // null = not yet detected

    function detectScrollbarWidth() {
        var outer = document.createElement('div');
        outer.style.cssText = 'visibility:hidden;overflow:scroll;width:100px;position:absolute;top:-9999px';
        document.body.appendChild(outer);
        var inner = document.createElement('div');
        inner.style.width = '100%';
        outer.appendChild(inner);
        scrollbarWidth = outer.offsetWidth - inner.offsetWidth;
        document.body.removeChild(outer);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', detectScrollbarWidth);
    } else {
        detectScrollbarWidth();
    }

    // Mark that this page has the left scrollbar fix enabled
    window.leftScrollbarFixEnabled = true;

    window.adjustLeftScrollbarHeader = function(tableId) {
        // Detect lazily in case called before DOMContentLoaded
        if (scrollbarWidth === null) detectScrollbarWidth();
        // Overlay scrollbars (width 0) need no adjustment
        if (scrollbarWidth === 0) return;

        var wrapper = tableId ? $('#' + tableId + '_wrapper') : $('.dataTables_wrapper');
        var scrollHeadInner = wrapper.find('.dataTables_scrollHeadInner');
        var headerTable = wrapper.find('.dataTables_scrollHead table');
        var bodyTableWidth = wrapper.find('.dataTables_scrollBody table').width();
        
        headerTable[0].style.cssText += 'width:' + bodyTableWidth + 'px !important;';
        scrollHeadInner[0].style.cssText += 'width:' + (bodyTableWidth + scrollbarWidth) + 'px !important;margin-left:' + scrollbarWidth + 'px !important;';
    };
})();
