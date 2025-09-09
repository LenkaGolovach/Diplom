<template>
  <div class="search-tasks">
    <div class="search-container">
      <div class="search-input-wrapper">
        <svg class="svg-search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Поиск задач..."
          class="search-input"
          @input="debouncedSearch"
        />
      </div>
      <div class="filters">
        <select v-model="selectedBoard" class="filter-select">
          <option value="">Все доски</option>
          <option v-for="board in boards" :key="board.id" :value="board.id">
            {{ board.name }}
          </option>
        </select>
        <select v-model="selectedColumnName" class="filter-select">
          <option value="">Все колонки</option>
          <option value="Нужно сделать">Нужно сделать</option>
          <option value="В процессе">В процессе</option>
          <option value="Готово">Готово</option>
          <option value="__other__">Другие</option>
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
            placeholder="Создано с..."
            class="date-input"
            title="Создано с"
          />
          <input
            type="date"
            v-model="createdBefore"
            placeholder="Создано по..."
            class="date-input"
            title="Создано по"
          />
        </div>
        <button @click="clearFilters" class="clear-filters-button">Очистить фильтры</button>
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
import { ref, watch, onMounted } from 'vue'
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
    const selectedColumnName = ref('')
    const selectedPriority = ref('')
    const createdAfter = ref('')
    const createdBefore = ref('')
    const tasks = ref([])
    const boards = ref([])
    const columns = ref([])

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
          column_name: selectedColumnName.value,
          priority: selectedPriority.value,
          created_after: createdAfter.value,
          created_before: createdBefore.value
        }

        Object.keys(params).forEach(key => {
          if (params[key] === null || params[key] === '') {
            delete params[key];
          }
        });

        console.log("Search Params:", params);

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

    const clearFilters = () => {
      searchQuery.value = ''
      selectedBoard.value = ''
      selectedColumnName.value = ''
      selectedPriority.value = ''
      createdAfter.value = ''
      createdBefore.value = ''
    }

    watch(selectedBoard, (newBoard) => {
      selectedColumnName.value = ''
      searchTasks()
    })

    watch([selectedColumnName, selectedPriority, createdAfter, createdBefore], () => {
      searchTasks()
    })

    onMounted(async () => {
      await loadBoards();
      await loadColumns();
      await searchTasks();
    });

    return {
      searchQuery,
      selectedBoard,
      selectedColumnName,
      selectedPriority,
      createdAfter,
      createdBefore,
      tasks,
      boards,
      columns,
      getColumnName,
      getBoardName,
      formatDate,
      debouncedSearch,
      goToTask,
      getPriorityClass,
      getPriorityText,
      clearFilters
    }
  }
}
</script>

<style scoped>
.search-tasks {
  display: flex;
  flex-direction: column;
  gap: 25px; /* Пространство между блоком фильтров и результатами */
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  padding: 10px; /* Небольшой внутренний отступ для всего компонента */
}

.search-container {
  background-color: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.search-input-wrapper {
  position: relative;
}

.svg-search-icon {
  position: absolute;
  left: 12px; /* Отступ слева для иконки */
  top: 50%;
  transform: translateY(-50%);
  width: 16px; /* Размер иконки */
  height: 16px;
  color: #909399; /* Цвет иконки */
  stroke-width: 2.5; /* Толщина линий для этого SVG */
}

.search-input {
  width: 100%;
  padding: 12px 15px 12px 40px; /* Отступ слева для иконки */
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  font-size: 1rem;
  color: #303133;
  box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
  align-items: center;
}

.filter-select, .date-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #606266;
  background-color: #fff;
  box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s;
  height: 40px; /* Фиксированная высота для единообразия */
}

.filter-select:focus, .date-input:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.date-filters {
  display: contents; /* Позволяет инпутам даты быть частью грида */
}

.search-results {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.task-card {
  background-color: #fff;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.task-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.task-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  word-break: break-word;
}

.priority-label {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  margin-left: 10px;
  flex-shrink: 0;
  color: #fff;
}

.priority-high { background-color: #f56c6c; }
.priority-medium { background-color: #e6a23c; }
.priority-low { background-color: #67c23a; }

.task-card p {
  font-size: 0.9rem;
  color: #5a6370;
  margin-bottom: 12px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2; /* Ограничение в 2 строки для описания */
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 2.7em; /* Примерная высота для двух строк */
}

.task-meta {
  font-size: 0.8rem;
  color: #8892a0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-meta span {
  display: block;
}

.no-results {
  text-align: center;
  padding: 30px;
  font-size: 1.1rem;
  color: #8892a0;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.clear-filters-button {
  padding: 10px 15px;
  border: 1px solid #dcdfe6;
  background-color: #f5f7fa;
  color: #606266;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
  text-align: center;
  white-space: nowrap;
  height: 40px;
  box-sizing: border-box;
}

.clear-filters-button:hover {
  background-color: #e4e7ed;
  border-color: #c0c4cc;
  color: #303133;
}

.clear-filters-button:focus {
    outline: none;
    border-color: #409eff;
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.date-input {
  color-scheme: light;
}
</style> 