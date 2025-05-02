<template>
  <div class="search-tasks">
    <div class="search-container">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Поиск задач..."
        class="search-input"
        @input="debouncedSearch"
      />
      <div class="filters">
        <select v-model="selectedBoard" class="filter-select">
          <option value="">Все доски</option>
          <option v-for="board in boards" :key="board.id" :value="board.id">
            {{ board.name }}
          </option>
        </select>
        <select v-model="selectedColumn" class="filter-select">
          <option value="">Все колонки</option>
          <option v-for="column in columns" :key="column.id" :value="column.id">
            {{ column.name }}
          </option>
        </select>
        <select v-model="selectedPriority" class="filter-select">
          <option value="">Все приоритеты</option>
          <option value="high">Высокий</option>
          <option value="medium">Средний</option>
          <option value="low">Низкий</option>
        </select>
        <div class="date-filters">
          <input
            type="date"
            v-model="createdAfter"
            placeholder="Создано после"
            class="date-input"
          />
          <input
            type="date"
            v-model="createdBefore"
            placeholder="Создано до"
            class="date-input"
          />
        </div>
      </div>
    </div>
    <div class="search-results" v-if="tasks.length > 0">
      <div 
        v-for="task in tasks" 
        :key="task.id" 
        class="task-card"
        @click="goToTask(task)"
      >
        <div class="task-header">
          <h3>{{ task.name }}</h3>
          <div class="priority-label" :class="getPriorityClass(task.priority)">
            {{ getPriorityText(task.priority) }}
          </div>
        </div>
        <p>{{ task.description }}</p>
        <div class="task-meta">
          <span>Колонка: {{ getColumnName(task.column) }}</span>
          <span>Доска: {{ getBoardName(task.column) }}</span>
          <span>Создано: {{ formatDate(task.created_at) }}</span>
        </div>
      </div>
    </div>
    <div v-else-if="searchQuery" class="no-results">
      Задачи не найдены
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import axios from 'axios'
import debounce from 'lodash/debounce'

export default {
  name: 'SearchTasks',
  setup() {
    const store = useStore()
    const router = useRouter()
    const searchQuery = ref('')
    const selectedBoard = ref('')
    const selectedColumn = ref('')
    const selectedPriority = ref('')
    const createdAfter = ref('')
    const createdBefore = ref('')
    const tasks = ref([])
    const boards = ref([])
    const columns = ref([])

    // Вычисляемое свойство для фильтрации колонок по выбранной доске
    const filteredColumns = computed(() => {
      if (!selectedBoard.value) return columns.value
      return columns.value.filter(column => column.board === selectedBoard.value)
    })

    const getPriorityClass = (priority) => {
      const classes = {
        high: 'priority-high',
        medium: 'priority-medium',
        low: 'priority-low'
      }
      return classes[priority] || ''
    }

    const getPriorityText = (priority) => {
      const texts = {
        high: 'Высокий',
        medium: 'Средний',
        low: 'Низкий'
      }
      return texts[priority] || 'Не указан'
    }

    const loadBoards = async () => {
      try {
        const response = await axios.get('/api/boards/', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        })
        boards.value = response.data
        console.log('Loaded boards:', boards.value)
      } catch (error) {
        console.error('Error loading boards:', error)
      }
    }

    const loadColumns = async () => {
      try {
        const response = await axios.get('/api/columns/', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        })
        columns.value = response.data
        console.log('Loaded columns:', columns.value)
      } catch (error) {
        console.error('Error loading columns:', error)
      }
    }

    const getColumnName = (columnId) => {
      const column = columns.value.find(c => c.id === columnId)
      return column ? column.name : ''
    }

    const getBoardName = (columnId) => {
      const column = columns.value.find(c => c.id === columnId)
      if (!column) return ''
      const board = boards.value.find(b => b.id === column.board)
      return board ? board.name : ''
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString()
    }

    const goToTask = (task) => {
      const column = columns.value.find(c => c.id === task.column)
      if (column) {
        console.log('Navigating to board:', column.board, 'with task:', task.id)
        router.push({
          path: `/boards/${column.board}`,
          query: { task: task.id }
        })
      } else {
        console.error('Column not found for task:', task)
      }
    }

    const searchTasks = async () => {
      try {
        const params = {
          search: searchQuery.value,
          board: selectedBoard.value,
          column: selectedColumn.value,
          priority: selectedPriority.value,
          created_after: createdAfter.value,
          created_before: createdBefore.value
        }

        const token = localStorage.getItem('token')
        const response = await axios.get('/api/tasks/', { 
          params,
          headers: {
            Authorization: `Bearer ${token}`
          }
        })
        tasks.value = response.data
      } catch (error) {
        console.error('Error searching tasks:', error)
        if (error.response && error.response.data && error.response.data.detail) {
          alert(error.response.data.detail)
        } else {
          alert('Произошла ошибка при поиске задач')
        }
      }
    }

    const debouncedSearch = debounce(searchTasks, 300)

    watch(selectedBoard, (newBoard) => {
      selectedColumn.value = ''
      searchTasks()
    })

    watch([selectedColumn, selectedPriority, createdAfter, createdBefore], () => {
      searchTasks()
    })

    loadBoards()
    loadColumns()

    return {
      searchQuery,
      selectedBoard,
      selectedColumn,
      selectedPriority,
      createdAfter,
      createdBefore,
      tasks,
      boards,
      columns: filteredColumns,
      getColumnName,
      getBoardName,
      formatDate,
      debouncedSearch,
      goToTask,
      getPriorityClass,
      getPriorityText
    }
  }
}
</script>

<style scoped>
.search-tasks {
  padding: 20px;
}

.search-container {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 10px;
}

.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-width: 150px;
}

.date-filters {
  display: flex;
  gap: 10px;
}

.date-input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.search-results {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.task-card {
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  transition: all 0.2s ease;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.task-header h3 {
  margin: 0;
  flex: 1;
}

.priority-label {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: bold;
  margin-left: 10px;
}

.priority-high {
  background-color: #ffebee;
  color: #d32f2f;
  border: 1px solid #ffcdd2;
}

.priority-medium {
  background-color: #fff3e0;
  color: #f57c00;
  border: 1px solid #ffe0b2;
}

.priority-low {
  background-color: #e8f5e9;
  color: #388e3c;
  border: 1px solid #c8e6c9;
}

.task-meta {
  margin-top: 10px;
  font-size: 0.9em;
  color: #666;
}

.task-meta span {
  display: block;
  margin-bottom: 5px;
}

.no-results {
  text-align: center;
  padding: 20px;
  color: #666;
}
</style> 