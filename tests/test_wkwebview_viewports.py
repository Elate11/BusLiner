import sys
import os
import json
import WebKit
import AppKit
import Foundation
from PyObjCTools import AppHelper

app = AppKit.NSApplication.sharedApplication()

viewports = [320, 375, 430, 768, 1024, 1440]
files = [
    "/Users/aleksandr/BusLiner/carrier-workspace.html",
    "/Users/aleksandr/BusLiner/carrier-dashboard.html",
    "/Users/aleksandr/BusLiner/passenger-cabinet.html"
]

all_results = []
current_task = [0, 0] # [file_idx, vp_idx]

class UniversalNavDelegate(Foundation.NSObject):
    def webView_didFinishNavigation_(self, wv, nav):
        file_idx, vp_idx = current_task
        file_path = files[file_idx]
        vp_width = viewports[vp_idx]
        
        js = """
        (() => {
            const docEl = document.documentElement;
            const body = document.body;
            const scrollW = Math.max(docEl.scrollWidth, body.scrollWidth);
            const clientW = docEl.clientWidth;
            const innerW = window.innerWidth;
            
            const overflowing = [];
            const all = document.querySelectorAll('*');
            for (let el of all) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                if (el.scrollWidth > clientW + 1 && style.overflowX !== 'hidden' && style.overflowX !== 'auto' && style.overflowX !== 'scroll') {
                    overflowing.push({
                        tag: el.tagName,
                        id: el.id || null,
                        cls: el.className ? String(el.className).substring(0, 50) : null,
                        scrollWidth: el.scrollWidth,
                        clientWidth: clientW,
                        rectRight: rect.right
                    });
                }
            }
            return {
                scrollW: scrollW,
                clientW: clientW,
                innerW: innerW,
                hasOverflow: scrollW > clientW,
                overflowingCount: overflowing.length,
                overflowingSample: overflowing.slice(0, 5)
            };
        })()
        """
        
        def completion_handler(val, err):
            filename = os.path.basename(file_path)
            res_entry = {
                "file": filename,
                "viewport": vp_width,
                "error": str(err) if err else None
            }
            if val:
                res_entry.update({
                    "scrollW": float(val.objectForKey_("scrollW")),
                    "clientW": float(val.objectForKey_("clientW")),
                    "innerW": float(val.objectForKey_("innerW")),
                    "hasOverflow": bool(val.objectForKey_("hasOverflow")),
                    "overflowingCount": int(val.objectForKey_("overflowingCount")),
                    "overflowingSample": [dict(x) for x in val.objectForKey_("overflowingSample")] if val.objectForKey_("overflowingSample") else []
                })
            all_results.append(res_entry)
            
            # Advance to next
            current_task[1] += 1
            if current_task[1] >= len(viewports):
                current_task[1] = 0
                current_task[0] += 1
                
            if current_task[0] >= len(files):
                print("JSON_START")
                print(json.dumps(all_results, indent=2))
                print("JSON_END")
                AppHelper.stopEventLoop()
                return
                
            run_next()

        wv.evaluateJavaScript_completionHandler_(js, completion_handler)

delegate_instance = UniversalNavDelegate.alloc().init()
active_webview = None

def run_next():
    global active_webview
    file_idx, vp_idx = current_task
    file_path = files[file_idx]
    width = viewports[vp_idx]
    height = 900 if width >= 768 else 844
    
    frame = Foundation.NSMakeRect(0, 0, width, height)
    config = WebKit.WKWebViewConfiguration.alloc().init()
    active_webview = WebKit.WKWebView.alloc().initWithFrame_configuration_(frame, config)
    active_webview.setNavigationDelegate_(delegate_instance)
    
    url = Foundation.NSURL.fileURLWithPath_(file_path)
    active_webview.loadFileURL_allowingReadAccessToURL_(url, url.URLByDeletingLastPathComponent())

run_next()
AppHelper.runConsoleEventLoop()
