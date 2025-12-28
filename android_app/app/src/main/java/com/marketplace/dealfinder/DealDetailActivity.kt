package com.marketplace.dealfinder

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.marketplace.dealfinder.api.ApiClient
import com.marketplace.dealfinder.models.Deal
import kotlinx.coroutines.launch

class DealDetailActivity : AppCompatActivity() {

    private lateinit var deal: Deal

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_deal_detail)

        deal = intent.getParcelableExtra("deal") ?: run {
            finish()
            return
        }

        setupUI()
    }

    private fun setupUI() {
        // Set action bar title
        supportActionBar?.title = "Deal Details"
        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        // Populate fields
        findViewById<TextView>(R.id.detailTitle).text = deal.title
        findViewById<TextView>(R.id.detailPrice).text = deal.getPriceString()
        findViewById<TextView>(R.id.detailSource).text = "Source: ${deal.source}"
        findViewById<TextView>(R.id.detailQuality).text = "Quality: ${deal.getQualityString()}"
        findViewById<TextView>(R.id.detailScore).text = "Score: ${deal.getScoreString()}"

        deal.location?.let {
            findViewById<TextView>(R.id.detailLocation).text = "Location: $it"
        }

        // Open listing button
        findViewById<Button>(R.id.openListingButton).setOnClickListener {
            openListing()
        }

        // Thumbs up button
        findViewById<Button>(R.id.thumbsUpButton).setOnClickListener {
            submitFeedback(true)
        }

        // Thumbs down button
        findViewById<Button>(R.id.thumbsDownButton).setOnClickListener {
            submitFeedback(false)
        }
    }

    private fun openListing() {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(deal.url))
        startActivity(intent)
    }

    private fun submitFeedback(isGoodDeal: Boolean) {
        lifecycleScope.launch {
            try {
                val deviceId = android.provider.Settings.Secure.getString(
                    contentResolver,
                    android.provider.Settings.Secure.ANDROID_ID
                )

                val request = mapOf(
                    "device_id" to deviceId,
                    "listing" to mapOf(
                        "title" to deal.title,
                        "price" to deal.price,
                        "url" to deal.url,
                        "source" to deal.source
                    ),
                    "is_good_deal" to isGoodDeal
                )

                val response = ApiClient.apiService.submitFeedback(request)
                if (response.isSuccessful) {
                    Toast.makeText(
                        this@DealDetailActivity,
                        "Thank you for your feedback!",
                        Toast.LENGTH_SHORT
                    ).show()

                    // Disable buttons after feedback
                    findViewById<Button>(R.id.thumbsUpButton).isEnabled = false
                    findViewById<Button>(R.id.thumbsDownButton).isEnabled = false
                } else {
                    Toast.makeText(
                        this@DealDetailActivity,
                        "Failed to submit feedback",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            } catch (e: Exception) {
                Toast.makeText(
                    this@DealDetailActivity,
                    "Error: ${e.message}",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}
