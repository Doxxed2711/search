package com.marketplace.dealfinder

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.marketplace.dealfinder.api.ApiClient
import kotlinx.coroutines.launch

class SettingsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        supportActionBar?.title = "Settings"
        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        loadStats()
    }

    private fun loadStats() {
        lifecycleScope.launch {
            try {
                val response = ApiClient.apiService.healthCheck()
                if (response.isSuccessful) {
                    response.body()?.let { health ->
                        val stats = health.ml_model_stats

                        val statsText = StringBuilder()
                        statsText.append("Server Status: ${health.status}\n\n")

                        stats?.let {
                            statsText.append("ML Model Statistics:\n")
                            statsText.append("Total Feedback: ${it["total_feedback"]}\n")
                            statsText.append("Good Deals: ${it["good_deals_marked"]}\n")
                            statsText.append("Bad Deals: ${it["bad_deals_marked"]}\n\n")

                            (it["model_weights"] as? Map<*, *>)?.let { weights ->
                                statsText.append("Model Weights:\n")
                                weights.forEach { (key, value) ->
                                    statsText.append("  $key: %.3f\n".format(value))
                                }
                            }
                        }

                        findViewById<TextView>(R.id.statsText).text = statsText.toString()
                    }
                }
            } catch (e: Exception) {
                findViewById<TextView>(R.id.statsText).text = "Error loading stats: ${e.message}"
            }
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}
