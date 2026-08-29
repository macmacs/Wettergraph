package io.github.macmacs.af;

import android.app.Activity;
import android.appwidget.AppWidgetManager;
import android.content.ComponentName;
import android.os.Bundle;

/**
 * Debug-only helper used by the screenshot capture pipeline: requests that the
 * launcher pin a Wettergraph widget, which lands on the home screen after the
 * user (or UI automation) confirms the launcher dialog.
 */
public class AfWidgetPinActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        AppWidgetManager.getInstance(this).requestPinAppWidget(
                new ComponentName(this, AfWidget.class), null, null);
        finish();
    }
}
