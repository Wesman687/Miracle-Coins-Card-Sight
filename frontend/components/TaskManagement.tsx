import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { 
  ClipboardDocumentListIcon,
  PlayIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  PlusIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface Task {
  task_id: string
  summary: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  priority: 'high' | 'medium' | 'low'
  created_at: string
  updated_at: string
  dependencies?: string[]
  deliverables?: string[]
}

interface TaskManagementProps {
  onClose?: () => void
}

export default function TaskManagement({ onClose }: TaskManagementProps) {
  const [selectedStatus, setSelectedStatus] = useState<string>('')
  const [showCreateTask, setShowCreateTask] = useState(false)
  const queryClient = useQueryClient()

  // Fetch tasks
  const { data: tasks, isLoading, refetch } = useQuery(
    ['tasks', selectedStatus],
    () => api.get(`/tasks${selectedStatus ? `?status=${selectedStatus}` : ''}`),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  )

  // Get next task
  const { data: nextTask } = useQuery(
    'next-task',
    () => api.get('/tasks/next'),
    {
      refetchInterval: 60000, // Refetch every minute
    }
  )

  // Update task status mutation
  const updateStatusMutation = useMutation(
    ({ taskId, status, notes }: { taskId: string; status: string; notes?: string }) =>
      api.put(`/tasks/${taskId}/status`, { status, notes }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['tasks'])
        toast.success('Task status updated!')
      },
      onError: () => {
        toast.error('Failed to update task status')
      },
    }
  )

  // Execute task mutation
  const executeTaskMutation = useMutation(
    (taskId: string) => api.post(`/tasks/execute/${taskId}`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['tasks'])
        toast.success('Task execution initiated!')
      },
      onError: () => {
        toast.error('Failed to execute task')
      },
    }
  )

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-400" />
      case 'in_progress':
        return <PlayIcon className="h-5 w-5 text-blue-400" />
      case 'pending':
        return <ClockIcon className="h-5 w-5 text-yellow-400" />
      case 'cancelled':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'text-red-400 bg-red-500/10'
      case 'medium':
        return 'text-yellow-400 bg-yellow-500/10'
      case 'low':
        return 'text-green-400 bg-green-500/10'
      default:
        return 'text-gray-400 bg-gray-500/10'
    }
  }

  const handleStatusUpdate = (taskId: string, newStatus: string) => {
    updateStatusMutation.mutate({ taskId, status: newStatus })
  }

  const handleExecuteTask = (taskId: string) => {
    executeTaskMutation.mutate(taskId)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500 mx-auto"></div>
        <p className="mt-2 text-gray-400">Loading tasks...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-yellow-500 flex items-center">
          <ClipboardDocumentListIcon className="h-6 w-6 mr-2" />
          Task Management
        </h2>
        <div className="flex items-center space-x-4">
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
          >
            <option value="">All Tasks</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <button
            onClick={() => setShowCreateTask(true)}
            className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <PlusIcon className="h-4 w-4" />
            <span>New Task</span>
          </button>
        </div>
      </div>

      {/* Next Task */}
      {nextTask?.data && (
        <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-yellow-500 mb-4">Next Task</h3>
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="text-lg font-semibold text-white">
                  {nextTask.data.task_id}: {nextTask.data.summary}
                </h4>
                <p className="text-gray-400 mt-2">
                  Priority: <span className={getPriorityColor(nextTask.data.priority)}>
                    {nextTask.data.priority}
                  </span>
                </p>
              </div>
              <button
                onClick={() => handleExecuteTask(nextTask.data.task_id)}
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Execute
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tasks List */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Task
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Priority
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {tasks?.data?.map((task: Task) => (
                <tr key={task.task_id} className="hover:bg-gray-750 transition-colors">
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-white">
                        {task.task_id}
                      </div>
                      <div className="text-sm text-gray-400">
                        {task.summary}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(task.status)}
                      <span className="text-sm text-gray-300 capitalize">
                        {task.status.replace('_', ' ')}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-300">
                      {formatDate(task.created_at)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      {task.status === 'pending' && (
                        <button
                          onClick={() => handleStatusUpdate(task.task_id, 'in_progress')}
                          className="text-blue-400 hover:text-blue-300 transition-colors"
                          title="Start task"
                        >
                          <PlayIcon className="h-4 w-4" />
                        </button>
                      )}
                      {task.status === 'in_progress' && (
                        <button
                          onClick={() => handleStatusUpdate(task.task_id, 'completed')}
                          className="text-green-400 hover:text-green-300 transition-colors"
                          title="Complete task"
                        >
                          <CheckCircleIcon className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleExecuteTask(task.task_id)}
                        className="text-purple-400 hover:text-purple-300 transition-colors"
                        title="Execute task"
                      >
                        <PlayIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Task Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-yellow-400">
            {tasks?.data?.filter((t: Task) => t.status === 'pending').length || 0}
          </div>
          <div className="text-sm text-gray-400">Pending</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-400">
            {tasks?.data?.filter((t: Task) => t.status === 'in_progress').length || 0}
          </div>
          <div className="text-sm text-gray-400">In Progress</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-400">
            {tasks?.data?.filter((t: Task) => t.status === 'completed').length || 0}
          </div>
          <div className="text-sm text-gray-400">Completed</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-gray-400">
            {tasks?.data?.length || 0}
          </div>
          <div className="text-sm text-gray-400">Total</div>
        </div>
      </div>
    </div>
  )
}




