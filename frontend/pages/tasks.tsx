import type { NextPage } from 'next'
import Head from 'next/head'
import TaskManagement from '../components/TaskManagement'

const TasksPage: NextPage = () => {
  return (
    <div className="min-h-screen bg-black text-white">
      <Head>
        <title>Task Management - Miracle Coins CoinSync Pro</title>
        <meta name="description" content="AI task management system for Miracle Coins" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Header */}
      <header className="bg-gray-900 border-b border-yellow-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-yellow-500">Miracle Coins</h1>
              <span className="ml-2 text-sm text-gray-400">Task Management</span>
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
        <TaskManagement />
      </main>
    </div>
  )
}

export default TasksPage




