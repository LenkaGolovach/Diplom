<template>
  <div class="board" ref="boardContainer">
    <div class="board-header">
      <div class="board-title-wrapper">
        <div
          v-if="!isEditingBoardName"
          class="board-title"
          @dblclick="startEditingBoardName"
        >
          {{ truncatedBoardName }}
        </div>
        <input
          v-else
          ref="boardNameInput"
          v-model="board.name"
          @blur="stopEditingBoardName"
          @keyup.enter="stopEditingBoardName"
          class="board-title-input"
        />
        <div class="header-buttons">
          <button @click="showMembersModal = true" class="members-button header-button">
            👥 Участники
          </button>
          <button @click="generateBoardReport" class="report-button header-button">
            <i class="fas fa-chart-bar"></i> Отчёт по проекту
          </button>
          <button class="add-column-button header-button" @click="addColumn">
            + Добавить колонку
          </button>
        </div>
      </div>
    </div>

    <Toolbar 
      :currentTool="currentDrawingTool"
      @tool-selected="handleToolSelected"
    />

    <div class="columns-container" :style="columnsContainerStyle" ref="columnsContainerRef">
      <canvas 
        ref="drawingCanvas"
        :width="canvasWidth"
        :height="canvasHeight"
        class="drawing-canvas"
      ></canvas>
      <Column
        v-for="(column, index) in board.columns"
        :key="column.id"
        :column="column"
        @add-task="(taskName) => addTask(board.columns.findIndex(c => c.id === column.id), taskName)"
        @update-column="updateColumn"
        @delete-column="() => deleteColumnById(column.id)"
        @update-tasks="tasks => updateColumnTasksById(column.id, tasks)"
        @openTaskModal="openModal"
        @save-column-position="saveColumnPosition"
        @bring-to-front="bringColumnToFront"
      />
    </div>

    <TaskModal
      v-if="showModal"
      :task="currentTask"
      :board="board"
      :current-user="currentUser"
      @close="closeModal"
      @saveTask="saveTask"
      @members-changed="fetchBoardData"
    />

    <BoardMembersModal
      v-if="showMembersModal"
      :board="board"
      :current-user="currentUser"
      @close="showMembersModal = false"
      @update-members="fetchBoardData"
    />
  </div>
</template>

<script>
import Column from '../components/Column.vue';
import BoardMembersModal from '../components/BoardMembersModal.vue'
import TaskModal from '../components/TaskModal.vue';
import Toolbar from '../components/Toolbar.vue';
import axios from 'axios';
import { reactive } from 'vue';
import Vue from 'vue';
import * as XLSX from 'xlsx';

const COLORS = [
  '#61bd4f', '#f2d600', 
  '#ff9f1a', '#eb5a46', 
  '#c377e0', '#0079bf'
];

export default {
  components: {
    Column,
    TaskModal,
    BoardMembersModal,
    Toolbar,
  },
  props: {
    id: {
      type: [String, Number],
      required: true,
    },
  },
  data() {
    return {
      board: reactive({
        name: '',
        columns: [],
      }),
      showModal: false,
      currentTask: {
        id: null,
        name: '',
        description: '',
        subtasks: [],
        files: [],
      },
      currentColumnIndex: null,
      isEditingBoardName: false,
      showMembersModal: false,
      currentUser: null,
      // --- New properties for pan and zoom ---
      scale: 1,
      translateX: 0,
      translateY: 0,
      isPanning: false,
      panStartX: 0,
      panStartY: 0,
      // --- End of new properties ---
      // --- Properties for drawing ---
      currentDrawingTool: 'cursor',
      canvasWidth: 5000, // Начальная ширина холста
      canvasHeight: 5000, // Начальная высота холста
      drawingContext: null,
      isDrawing: false, // Флаг, идет ли рисование
      drawingData: [], // Массив для хранения всех нарисованных элементов
      currentStroke: null, // Текущий рисуемый штрих
      // --- End of drawing properties ---
    };
  },
  computed: {
    truncatedBoardName() {
      return this.board.name.length > 20 
        ? this.board.name.substring(0, 17) + '...' 
        : this.board.name
    },
    // --- New computed property for pan and zoom ---
    columnsContainerStyle() {
      return {
        transform: `translate(${this.translateX}px, ${this.translateY}px) scale(${this.scale})`,
        transformOrigin: '0 0', 
      };
    }
    // --- End of new computed property ---
  },
  watch: {
    // Добавляем наблюдатель за параметрами URL
    '$route.query': {
      handler(query) {
        if (query.task) {
          this.openTaskFromQuery(query.task);
        }
      },
      immediate: true
    }
  },
  async created() {
    console.log('Board component created with id:', this.id)
    await this.fetchUser();
    await this.fetchBoardData();
  },
  mounted() {
    this.$el.addEventListener('wheel', this.handleWheel, { passive: false });
    this.$el.addEventListener('mousedown', this.handleMouseDown);

    // Инициализация холста
    const canvas = this.$refs.drawingCanvas;
    if (canvas) {
      this.drawingContext = canvas.getContext('2d');
      console.log('Drawing canvas initialized', this.drawingContext);
      // Тут можно будет установить начальные стили для рисования, если нужно
      this.redrawCanvas(); // Первоначальная перерисовка (если есть сохраненные данные)
    } else {
      console.error('Drawing canvas not found');
    }
    window.addEventListener('resize', this.handleResize);
    this.handleResize(); // Initial call to set up sizes or transforms if needed
  },
  beforeUnmount() {
    this.$el.removeEventListener('wheel', this.handleWheel);
    this.$el.removeEventListener('mousedown', this.handleMouseDown);
    
    document.removeEventListener('mousemove', this.handleMouseMove);
    document.removeEventListener('mouseup', this.handleMouseUp);
    if (this.isPanning) {
        this.$el.style.cursor = 'grab';
    }
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    async fetchUser() {
      try {
        const response = await axios.get('/api/users/me/', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        })
        this.currentUser = response.data
      } catch (error) {
        console.error('Ошибка загрузки пользователя:', error)
      }
    },
    async fetchBoardData() {
      try {
        console.log('Fetching board data for id:', this.id)
        const response = await axios.get(`/api/boards/${this.id}/`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
          params: { include_tasks: true }
        });
        console.log('Board data received:', response.data);
        
        let defaultX = 20;
        let defaultY = 20;
        let defaultZ = 1;
        const spacingX = 340; // Ширина колонки (300) + отступ (40)

        this.board = {
          ...response.data,
          columns: response.data.columns.map((column, index) => {
            // Приоритет координатам с бэкенда, если они есть
            const x = column.x_coord !== undefined && column.x_coord !== null ? column.x_coord : defaultX + index * spacingX;
            const y = column.y_coord !== undefined && column.y_coord !== null ? column.y_coord : defaultY;
            const z = column.z_index !== undefined && column.z_index !== null ? column.z_index : defaultZ + index;
            return {
              ...column,
              tasks: column.tasks || [],
              x: x,
              y: y,
              zIndex: z
            };
          })
        };
        this.board.columns.forEach(col => { col.tasks = col.tasks || []; });

        // Загружаем данные рисунков
        this.drawingData = response.data.drawing_data || [];
        this.redrawCanvas(); // Перерисовываем холст с загруженными данными

      } catch (error) {
        console.error('Ошибка загрузки доски:', error);
        if (error.response) {
          console.error('Response data:', error.response.data);
          console.error('Response status:', error.response.status);
        }
      }
    },
    async saveBoard() {
      try {
        await axios.put(`/api/boards/${this.id}/`, this.board, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
      } catch (error) {
        console.error('Ошибка сохранения доски:', error);
      }
    },
    startEditingBoardName() {
      this.isEditingBoardName = true;
      this.$nextTick(() => {
        this.$refs.boardNameInput.focus();
      });
    },
    async stopEditingBoardName() {
      this.isEditingBoardName = false;
      await this.saveBoard();
    },
    async addColumn() {
      const color = COLORS[this.board.columns.length % COLORS.length];
      
      let newX = 20;
      let newY = 20;
      if (this.board.columns.length > 0) {
        newX = Math.max(...this.board.columns.map(c => c.x)) + 340; 
      }
      const maxZ = this.board.columns.length > 0 ? Math.max(...this.board.columns.map(c => c.zIndex)) : 0;

      const newColumnData = {
        name: 'Новая колонка',
        color,
        board: this.board.id,
        // x_coord: newX, // Бэкенд должен сам назначить координаты или принять их
        // y_coord: newY,
        // z_index: maxZ + 1
      };

      try {
        const response = await axios.post('/api/columns/', newColumnData, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        const createdColumn = response.data;
        
        this.board.columns.push({
          ...createdColumn,
          tasks: [],
          x: createdColumn.x_coord !== undefined ? createdColumn.x_coord : newX,
          y: createdColumn.y_coord !== undefined ? createdColumn.y_coord : newY,
          zIndex: createdColumn.z_index !== undefined ? createdColumn.z_index : maxZ + 1
        });
      } catch (error) {
        console.error('Ошибка создания колонки:', error.response ? error.response.data : error.message);
      }
    },
    async deleteColumn(columnIndex) {
      const column = this.board.columns[columnIndex];
      try {
        await axios.delete(`/api/columns/${column.id}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        this.board.columns.splice(columnIndex, 1);
      } catch (error) {
        const errorMessage = error.response && error.response.data 
          ? error.response.data 
          : error.message;
        console.error('Ошибка загрузки досок:', errorMessage);
      }
    },
    updateColumn(updatedColumn) {
      const index = this.board.columns.findIndex(col => col.id === updatedColumn.id);
      if (index !== -1) {
        this.board.columns[index] = updatedColumn;
      }
    },
    addTask(columnIndex, taskName = '') {
      this.currentTask = {
        name: taskName,
        description: '',
        subtasks: [],
        files: [],
        column: this.board.columns[columnIndex].id, 
      };
      this.currentColumnIndex = columnIndex;
      this.showModal = true;
    },
    async saveTask(taskToSave) {
      // Логика сохранения задачи (создание или обновление)
      // ... (код был длинным, поэтому сокращен)
      this.closeModal();
      await this.fetchBoardData(); // Перезагружаем данные доски
    },
    updateColumnTasks(columnIndex, newTasks) {
      if (this.board.columns[columnIndex]) {
        this.board.columns[columnIndex].tasks = newTasks;
      }
    },
    openModal(task) {
      this.currentTask = { ...task };
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
      this.currentTask = {
        id: null,
        name: '',
        description: '',
        subtasks: [],
        files: [],
      };
      this.currentColumnIndex = null;
    },
    // Добавляем метод для открытия задачи из URL
    async openTaskFromQuery(taskId) {
      try {
        const response = await axios.get(`/api/tasks/${taskId}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        this.currentTask = response.data;
        this.showModal = true;
      } catch (error) {
        console.error('Ошибка загрузки задачи:', error);
      }
    },
    async generateBoardReport() {
      try {
        const response = await axios.get(`/api/reports/`, {
          params: {
            report_type: 'projects',
            board_id: this.id
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        // Создаем рабочую книгу Excel
        const ws = XLSX.utils.json_to_sheet(response.data.projects);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Board Report');
        
        // Добавляем лист с общей статистикой
        const summaryData = [
          ['Всего проектов', response.data.statistics.total_projects],
          ['Активных проектов', response.data.statistics.active_projects],
          ['Завершённых проектов', response.data.statistics.completed_projects]
        ];
        const summaryWs = XLSX.utils.aoa_to_sheet(summaryData);
        XLSX.utils.book_append_sheet(wb, summaryWs, 'Summary');
        
        // Генерируем имя файла с датой
        const date = new Date().toISOString().split('T')[0];
        const filename = `board_report_${this.id}_${date}.xlsx`;
        
        // Скачиваем файл
        XLSX.writeFile(wb, filename);
      } catch (error) {
        console.error('Ошибка при формировании отчёта:', error);
        if (error.response) {
          console.error('Response data:', error.response.data);
          console.error('Response status:', error.response.status);
        }
        alert('Произошла ошибка при формировании отчёта. Пожалуйста, попробуйте снова.');
      }
    },
    async saveColumnPosition(columnToSave) {
      console.log(`Saving position for column ${columnToSave.id}: X=${columnToSave.x}, Y=${columnToSave.y}, Z=${columnToSave.zIndex}`);
      try {
        await axios.patch(`/api/columns/${columnToSave.id}/`, {
          name: columnToSave.name,
          x_coord: columnToSave.x,
          y_coord: columnToSave.y,
          z_index: columnToSave.zIndex 
        }, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        const index = this.board.columns.findIndex(c => c.id === columnToSave.id);
        if (index !== -1) {
           // Убедимся, что локальный объект обновлен, если Vue не сделал это по ссылке
           this.board.columns.splice(index, 1, { ...this.board.columns[index], ...columnToSave });
        }
      } catch (error) {
        console.error(`Ошибка сохранения позиции для колонки ${columnToSave.id}:`, error.response ? error.response.data : error.message);
      }
    },
    deleteColumnById(columnId) {
      const columnIndex = this.board.columns.findIndex(c => c.id === columnId);
      if (columnIndex !== -1) {
        this.deleteColumn(columnIndex);
      } 
    },
    updateColumnTasksById(columnId, newTasks) {
      const columnIndex = this.board.columns.findIndex(c => c.id === columnId);
      if (columnIndex !== -1) {
        this.updateColumnTasks(columnIndex, newTasks);
      }
    },
    bringColumnToFront(columnId) {
      const columnToElevate = this.board.columns.find(c => c.id === columnId);
      if (!columnToElevate) return;

      const maxZ = Math.max(0, ...this.board.columns.map(c => c.zIndex || 0));
      
      if (columnToElevate.zIndex <= maxZ) {
          columnToElevate.zIndex = maxZ + 1;
      }
    },
    // --- New methods for pan and zoom ---
    handleWheel(event) {
      if (event.ctrlKey) {
        event.preventDefault();
        const zoomIntensity = 0.05; // Smaller intensity for smoother zoom
        const dir = event.deltaY > 0 ? -1 : 1;

        const boardRect = this.$el.getBoundingClientRect();
        const mouseX = event.clientX - boardRect.left; // Mouse X relative to the board div
        const mouseY = event.clientY - boardRect.top;  // Mouse Y relative to the board div

        const oldScale = this.scale;
        
        let newScale = oldScale + dir * zoomIntensity * oldScale;
        newScale = Math.max(0.2, Math.min(newScale, 3)); // Clamp scale (e.g., 20% to 300%)

        // Adjust translation to zoom towards the mouse point
        // Formula: newTranslate = mousePos - (mousePos - oldTranslate) * (newScale / oldScale)
        this.translateX = mouseX - (mouseX - this.translateX) * (newScale / oldScale);
        this.translateY = mouseY - (mouseY - this.translateY) * (newScale / oldScale);
        this.scale = newScale;
      }
      // If Ctrl is not pressed, default wheel behavior (e.g. scrolling if an element inside is scrollable) might occur.
      // Since columns-container is now overflow:visible, this primarily affects page scroll if board itself isn't filling viewport.
    },
    handleMouseDown(event) {
      // Middle mouse button (button === 1) for panning
      if (event.button === 1) { 
        event.preventDefault();
        this.isPanning = true;
        // Store initial mouse position relative to the current translation state
        this.panStartX = event.clientX - this.translateX;
        this.panStartY = event.clientY - this.translateY;
        
        this.$el.style.cursor = 'grabbing';

        document.addEventListener('mousemove', this.handleMouseMove);
        document.addEventListener('mouseup', this.handleMouseUp);
      }
    },
    handleMouseMove(event) {
      if (this.isPanning) {
        event.preventDefault(); // Prevent text selection, etc.
        this.translateX = event.clientX - this.panStartX;
        this.translateY = event.clientY - this.panStartY;
      }
    },
    handleMouseUp(event) {
      if (this.isPanning) {
        this.isPanning = false;
        this.$el.style.cursor = 'grab';

        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('mouseup', this.handleMouseUp);
      }
    },
    // --- End of new methods ---
    // --- Methods for drawing tools ---
    handleToolSelected(toolName) {
      this.currentDrawingTool = toolName;
      console.log('Tool selected:', toolName);
      const canvasEl = this.$refs.drawingCanvas;

      // Удаляем предыдущие слушатели, чтобы избежать дублирования
      canvasEl.removeEventListener('mousedown', this.canvasMouseDown);
      canvasEl.removeEventListener('mousemove', this.canvasMouseMove);
      // mouseup слушаем на window, чтобы поймать отпускание кнопки даже вне холста
      window.removeEventListener('mouseup', this.canvasMouseUp); 

      if (toolName === 'pencil' || toolName === 'line') {
        canvasEl.style.pointerEvents = 'auto';
        canvasEl.style.cursor = 'crosshair';
        // Добавляем слушатели для рисования
        canvasEl.addEventListener('mousedown', this.canvasMouseDown);
        // mousemove и mouseup будут добавляться/удаляться динамически в mousedown/mouseup
      } else {
        canvasEl.style.pointerEvents = 'none';
        canvasEl.style.cursor = 'default';
        this.isDrawing = false; // На всякий случай сбрасываем флаг рисования
      }
    },
    handleResize() {
      // Этот метод может понадобиться для адаптации холста или других элементов при изменении размера окна
      // Например, если бы холст должен был точно соответствовать видимой области columns-container.
      // В текущей реализации с большим фиксированным холстом внутри columns-container, он может быть не так критичен
      // для самого размера canvas, но может быть полезен для перерасчета каких-то элементов.
      // console.log('Window resized');
    },
    // --- Drawing implementation methods ---
    canvasMouseDown(event) {
      if (this.currentDrawingTool === 'pencil') {
        if (event.button !== 0) return; // Рисуем только левой кнопкой

        this.isDrawing = true;
        const { offsetX, offsetY } = event;

        // Создаем новый штрих
        this.currentStroke = {
          type: 'pencil',
          points: [{ x: offsetX, y: offsetY }],
          color: 'black', // В будущем будет настраиваемым
          lineWidth: 2,    // В будущем будет настраиваемым
          lineCap: 'round',
          lineJoin: 'round' 
        };
        
        // Начинаем рисовать на холсте немедленно (для текущего штриха)
        this.drawingContext.beginPath();
        this.drawingContext.moveTo(offsetX, offsetY);
        this.drawingContext.strokeStyle = this.currentStroke.color;
        this.drawingContext.lineWidth = this.currentStroke.lineWidth;
        this.drawingContext.lineCap = this.currentStroke.lineCap;
        this.drawingContext.lineJoin = this.currentStroke.lineJoin;

        this.$refs.drawingCanvas.addEventListener('mousemove', this.canvasMouseMove);
        window.addEventListener('mouseup', this.canvasMouseUp); 
      }
    },
    canvasMouseMove(event) {
      if (!this.isDrawing || this.currentDrawingTool !== 'pencil' || !this.currentStroke) return;
      
      const { offsetX, offsetY } = event;
      this.currentStroke.points.push({ x: offsetX, y: offsetY });

      // Продолжаем рисовать текущий путь
      this.drawingContext.lineTo(offsetX, offsetY);
      this.drawingContext.stroke();
    },
    canvasMouseUp(event) {
      if (this.isDrawing && this.currentDrawingTool === 'pencil') {
        if (event.button !== 0 && event.type === 'mouseup') return; 
        
        this.isDrawing = false;
        if (this.currentStroke && this.currentStroke.points.length > 1) {
          this.drawingData.push(this.currentStroke);
          console.log('Drawing data updated:', this.drawingData);
          this.saveDrawingData(); // Сохраняем данные на бэкенд
        }
        this.currentStroke = null;
        
        this.$refs.drawingCanvas.removeEventListener('mousemove', this.canvasMouseMove);
        window.removeEventListener('mouseup', this.canvasMouseUp);
      }
    },
    // --- End of Drawing implementation methods ---
    // --- Method to redraw canvas from drawingData ---
    redrawCanvas() {
      if (!this.drawingContext) return;
      // Очищаем холст
      this.drawingContext.clearRect(0, 0, this.canvasWidth, this.canvasHeight);

      this.drawingData.forEach(stroke => {
        if (stroke.type === 'pencil') {
          this.drawingContext.beginPath();
          this.drawingContext.moveTo(stroke.points[0].x, stroke.points[0].y);
          
          this.drawingContext.strokeStyle = stroke.color;
          this.drawingContext.lineWidth = stroke.lineWidth;
          this.drawingContext.lineCap = stroke.lineCap; // Убедимся, что эти свойства применяются
          this.drawingContext.lineJoin = stroke.lineJoin; // для каждого штриха

          for (let i = 1; i < stroke.points.length; i++) {
            this.drawingContext.lineTo(stroke.points[i].x, stroke.points[i].y);
          }
          this.drawingContext.stroke();
        }
        // В будущем здесь будут другие типы: line, rectangle и т.д.
      });
    },
    // --- End of redraw method ---
    // --- Method to save drawing data to backend ---
    async saveDrawingData() {
      if (!this.board.id) return; // Не сохраняем, если нет ID доски
      try {
        await axios.patch(`/api/boards/${this.board.id}/`, {
          drawing_data: this.drawingData
        }, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        console.log('Drawing data saved to backend.');
      } catch (error) {
        console.error('Ошибка сохранения данных рисунков:', error.response ? error.response.data : error.message);
      }
    }
    // --- End of save drawing data method ---
  },
};
</script>

<style scoped>
.board {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, 
    #ffffff 0%,
    #fff5f5 25%,
    #f8f7ff 50%,
    #fff5f5 75%,
    #ffffff 100%
  );
  cursor: grab; /* Indicate pannable area */
}

.board:active {
  /* cursor: grabbing;  -- Handled by JS for more control */
}

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  position: relative; /* Для z-index, если нужно, чтобы хедер был выше колонок */
  z-index: 100; /* Произвольное значение, выше чем у колонок по умолчанию */
}

.board-title-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
}

.board-title {
  font-size: 1.8em;
  font-weight: 600;
  color: #2c3e50;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 8px;
  transition: background-color 0.2s ease;
  margin-right: auto; /* Заголовок слева */
}

.board-title:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.board-title-input {
  font-size: 1.8em;
  font-weight: 600;
  color: #2c3e50;
  padding: 5px 10px;
  border: 1px solid #ccc;
  border-radius: 8px;
  margin-right: auto; /* Заголовок слева */
}

.header-buttons {
  display: flex;
  gap: 15px; /* Отступы между кнопками */
  margin-left: 20px; /* Отступ от заголовка */
}

/* --- ДОБАВЛЕННЫЕ/ИЗМЕНЕННЫЕ СТИЛИ --- */
.header-button { /* Общий стиль для кнопок в хедере */
  padding: 10px 18px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px; /* Отступ между иконкой и текстом */
  background: rgba(240, 242, 245, 0.8); /* Светло-серый фон */
  color: #4a5568; /* Темно-серый текст */
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.header-button:hover {
  background: rgba(230, 232, 235, 0.9);
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
}

.members-button {
  /* Убираем специфичные стили, если они были */
}

.report-button {
  /* Убираем старые стили, если они тут были */
  /* background: #4CAF50; - УДАЛЕНО */
  /* color: white; - УДАЛЕНО */
}

.report-button i {
  font-size: 1.1em;
}

.add-column-button {
  /* Оставляем специфичный синий фон */
  background: rgba(91, 156, 255, 0.9); 
  color: white;
  box-shadow: 0 2px 8px rgba(91, 156, 255, 0.3);
}

.add-column-button:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91, 156, 255, 0.4);
}
/* --- КОНЕЦ ДОБАВЛЕННЫХ/ИЗМЕНЕННЫХ СТИЛЕЙ --- */

.columns-container {
  flex: 1;
  padding: 20px;
  position: relative; 
  min-height: calc(100vh - 120px); 
  width: 100%; 
  box-sizing: border-box;
  /* overflow: auto; -- CHANGED */
  overflow: visible; /* Allow content to be transformed outside bounds */
}

.columns { 
  /* Этот класс больше не используется в шаблоне для оборачивания Column, если мы перешли на прямое позиционирование Column
     в .columns-container. Если он остался в шаблоне, его стили нужно пересмотреть. 
     Пока предполагаем, что <Column> рендерятся напрямую в .columns-container */
  width: 100%;
  height: 100%; /* Или min-content, чтобы контейнер рос по содержимому, если overflow:auto у родителя */
}

.members-button, .add-column-button {
  padding: 12px 18px;
  border: none;
  border-radius: 10px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-weight: 500;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  letter-spacing: 0.3px;
}

.members-button {
  background: #f0f0f0;
  color: #4a5568;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.members-button:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.07);
}

.add-column-button {
  background: #5b9cff;
  color: white;
  box-shadow: 0 4px 15px rgba(91, 156, 255, 0.3);
}

.add-column-button:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91, 156, 255, 0.4);
}

@media (max-width: 768px) {
  .board-header {
    padding: 16px 20px;
  }
  
  .board-title-wrapper {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .header-buttons {
    width: 100%;
    justify-content: flex-end;
  }
  
  .board-title-input {
    width: 100%;
  }
  
  .columns-container {
    padding: 20px;
  }
}

/* СТИЛИ НИЖЕ БУДУТ УДАЛЕНЫ */
/*
.report-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
  margin-left: 10px;
}

.report-button:hover {
  background-color: #45a049;
}
*/

.drawing-canvas {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 5; /* Должен быть выше колонок, но ниже UI элементов, если нужно */
  pointer-events: none; /* По умолчанию клики проходят сквозь */
}
</style>