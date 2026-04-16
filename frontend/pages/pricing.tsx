import type { NextPage } from 'next'
import Head from 'next/head'
import PricingDashboard from '../components/PricingDashboard'
import GeneralCategories from '../components/GeneralCategories'

const PricingPage: NextPage = () => {
  return (
    <div className="min-h-screen bg-black text-white">
      <Head>
        <title>Pricing Dashboard - Miracle Coins</title>
        <meta name="description" content="AI-powered pricing dashboard for Miracle Coins" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Header */}
      <header className="bg-gray-900 border-b border-yellow-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-yellow-500">Miracle Coins</h1>
              <span className="ml-2 text-sm text-gray-400">Pricing Dashboard</span>
            </div>
            <div className="flex items-center space-x-4">
              <a
                href="/"
                className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition-colors"
              >
                Back to Dashboard
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Pricing Dashboard - Takes up 2/3 of the width */}
          <div className="lg:col-span-2">
            <PricingDashboard />
          </div>

          {/* General Categories - Takes up 1/3 of the width */}
          <div className="lg:col-span-1">
            <GeneralCategories />
          </div>
        </div>
      </main>
    </div>
  )
}

export default PricingPage


