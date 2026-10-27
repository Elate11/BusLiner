import sys
import os
import json
import WebKit
import AppKit
import Foundation
from PyObjCTools import AppHelper

app = AppKit.NSApplication.sharedApplication()
file_path = "/Users/aleksandr/BusLiner/passenger-cabinet.html"

results = {}

class TestSeatDelegate(Foundation.NSObject):
    def webView_didFinishNavigation_(self, wv, nav):
        js = """
        (() => {
            const log = [];
            try {
                // 1. Open modal
                openBookingModal('BL-5715');
                log.push({ step: '1_open', selected: [...selectedSeatsForBooking] });

                // 2. Select seat via 2D chip element click
                const chip10 = document.getElementById('seatChip_10');
                if (chip10) {
                    chip10.click();
                    log.push({ step: '2_click_2d_chip_10', selected: [...selectedSeatsForBooking] });
                }

                // 3. Verify cross icon in chip container
                const chipsContainer = document.getElementById('selectedSeatsChips');
                const crossBefore = chipsContainer ? chipsContainer.querySelector('.chip-remove-icon') : null;
                log.push({ step: '3_check_cross', hasCross: !!crossBefore });

                // 4. Click cross icon to remove first seat
                if (crossBefore) {
                    crossBefore.click();
                    log.push({ step: '4_click_cross', selected: [...selectedSeatsForBooking] });
                }

                // 5. Test 3D seat selection via onSprinterSeatSelect (simulating 3D mesh click)
                window.onSprinterSeatSelect(12, null);
                log.push({ step: '5_3d_click_seat_12', selected: [...selectedSeatsForBooking] });

                // 6. Test deselecting seat 12 by clicking it again
                window.onSprinterSeatSelect(12, null);
                log.push({ step: '6_3d_click_seat_12_again', selected: [...selectedSeatsForBooking] });

                // 7. Remove all remaining seats via removeSelectedBookingSeat
                [...selectedSeatsForBooking].forEach(s => removeSelectedBookingSeat(s));
                log.push({ step: '7_all_removed', selectedCount: selectedSeatsForBooking.length });

                const submitBtn = document.getElementById('btnSubmitBooking');
                const isBtnDisabled = submitBtn ? submitBtn.disabled : null;

                // 8. Select seat 15 and confirm booking
                selectBookingSeat(15, '15A');
                submitBookingOrder();
                const storedBookings = getStoredBookings();
                const latest = storedBookings[0];
                const occupied = getOccupiedSeatsForTrip('BL-5715');

                return {
                    success: true,
                    log: log,
                    isBtnDisabledWhenEmpty: isBtnDisabled,
                    latestTicketSeat: latest ? latest.seat : null,
                    occupiedIncludes15A: occupied.includes('15A')
                };
            } catch (err) {
                return {
                    success: false,
                    error: err.toString(),
                    stack: err.stack,
                    log: log
                };
            }
        })();
        """

        def eval_callback(res, err):
            if err:
                print("JS_ERR:", err)
                results['error'] = str(err)
            else:
                try:
                    print("JS_RES:", res)
                    results['result'] = str(res)
                except Exception as ex:
                    print("PY_ERR:", ex)
                    results['error'] = str(ex)
            AppHelper.stopEventLoop()

        wv.evaluateJavaScript_completionHandler_(js, eval_callback)

del_obj = TestSeatDelegate.alloc().init()
config = WebKit.WKWebViewConfiguration.alloc().init()
wv = WebKit.WKWebView.alloc().initWithFrame_configuration_(((0, 0), (1200, 800)), config)
wv.setNavigationDelegate_(del_obj)
url = Foundation.NSURL.fileURLWithPath_(file_path)
wv.loadFileURL_allowingReadAccessToURL_(url, url.URLByDeletingLastPathComponent())

AppHelper.runConsoleEventLoop()

print("RESULTS_START")
print(json.dumps(results, indent=2, ensure_ascii=False))
print("RESULTS_END")
