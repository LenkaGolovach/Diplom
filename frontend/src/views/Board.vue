<template>
  <div class="board" ref="boardContainer">
    <!-- Фиксированные колонки показываем отдельно -->
    <div class="fixed-columns-container">
      <!-- Фиксированные колонки теперь показываются отдельно, чтобы они не зависели друг от друга -->
      <template v-for="column in fixedColumns" :key="column.id">
        <Column
          :column="column"
          :is-fixed-position="true"
          @add-task="(taskName) => addTask(board.columns.findIndex(c => c.id === column.id), taskName)"
          @update-column="updateColumn"
          @delete-column="() => deleteColumnById(column.id)"
          @update-tasks="tasks => updateColumnTasksById(column.id, tasks)"
          @openTaskModal="openModal"
          @save-column-position="saveColumnPosition"
          @bring-to-front="bringColumnToFront"
        />
      </template>
    </div>

    <div class="board-header">
      <div class="board-title-wrapper">
        <!-- Название доски перемещаем влево -->
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

        <!-- Добавляем таймер посередине -->
        <div class="timer-container">
          <div v-if="!timerActive" class="timer-display" @click="openTimerSettings">
            <i class="fas fa-clock"></i>
            <span>Установить таймер</span>
          </div>
          <div v-else class="timer-display timer-active" @click="stopTimer">
            <i class="fas fa-clock"></i>
            <span>{{ timerName }}: {{ formatTime(timerRemaining) }}</span>
            <i class="fas fa-stop-circle stop-icon"></i>
          </div>
        </div>

        <!-- Кнопки справа -->
        <div class="header-buttons">
          <button @click="showMembersModal = true" class="members-button header-button">
            <i class="fas fa-users"></i> Участники
          </button>
          <button @click="showHistoryModal = true" class="history-button header-button">
            <i class="fas fa-history"></i> История
          </button>
          <button @click="generateBoardReport" class="report-button header-button">
            <i class="fas fa-chart-bar"></i> Отчёт по проекту
          </button>
          <button class="add-column-button header-button" @click="addColumn">
            <i class="fas fa-plus"></i> Добавить колонку
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
        v-for="column in movableColumns"
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

    <BoardHistoryModal
      v-if="showHistoryModal"
      :board-id="board.id"
      :current-user="currentUser"
      @close="showHistoryModal = false"
    />

    <!-- Добавляем модальное окно подтверждения удаления колонки -->
    <ConfirmationModel
      v-if="showDeleteConfirmation"
      :title="'Удаление колонки'"
      :message="deleteConfirmationMessage"
      :confirmText="'Удалить'"
      :cancelText="'Отмена'"
      @confirm="confirmDeleteColumn"
      @close="cancelDeleteColumn"
    />

    <TimerEndDialog
      v-if="showTimerEndDialog"
      :timerName="timerName"
      @close="showTimerEndDialog = false"
    />

    <TimerSettingsModal
      v-if="showTimerSettings"
      :timerName="timerName"
      :timerHours="timerHours"
      :timerMinutes="timerMinutes"
      :timerSeconds="timerSeconds"
      @start="handleTimerStart"
      @cancel="closeTimerSettings"
    />
  </div>
</template>

<script>
import Column from '../components/Column.vue';
import BoardMembersModal from '../components/BoardMembersModal.vue'
import BoardHistoryModal from '@/components/BoardHistoryModal.vue';
import TaskModal from '../components/TaskModal.vue';
import Toolbar from '../components/Toolbar.vue';
import ConfirmationModel from '../components/ConfirmationModel.vue';
import TimerEndDialog from '../components/TimerEndDialog.vue';
import TimerSettingsModal from '../components/TimerSettingsModal.vue';
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
    BoardHistoryModal,
    Toolbar,
    ConfirmationModel,
    TimerEndDialog,
    TimerSettingsModal,
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
      showHistoryModal: false,
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
      lastEraserMoveTime: null, // Время последнего движения ластика
      lastEraserSaveTime: null, // Время последнего сохранения изменений ластика
      // --- End of drawing properties ---
      // --- Добавляем свойства для управления модальным окном подтверждения удаления колонки ---
      showDeleteConfirmation: false,
      columnToDelete: null,
      // --- Свойства для таймера ---
      showTimerSettings: false,
      timerName: 'Задача',
      timerActive: false,
      timerRemaining: 0,
      timerHours: 0,
      timerMinutes: 5,
      timerSeconds: 0,
      timerInterval: null,
      showTimerEndDialog: false
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
    },
    fixedColumns() {
      return this.board.columns.filter(column => 
        ['Нужно сделать', 'В процессе', 'Готово'].includes(column.name)
      );
    },
    movableColumns() {
      return this.board.columns.filter(column => 
        !['Нужно сделать', 'В процессе', 'Готово'].includes(column.name)
      );
    },
    // Вычисляемое свойство для формирования сообщения подтверждения удаления колонки
    deleteConfirmationMessage() {
      if (!this.columnToDelete) return '';
      
      const column = this.board.columns.find(c => c.id === this.columnToDelete);
      if (!column) return '';
      
      return `Вы действительно хотите удалить колонку "${column.name}"?`;
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
    
    // Добавляем обработчик клавиш для быстрого выбора инструментов
    window.addEventListener('keydown', this.handleKeyDown);
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
    window.removeEventListener('keydown', this.handleKeyDown);
    
    // Удаляем обработчики для рисования
    if (this.$refs.drawingCanvas) {
      this.$refs.drawingCanvas.removeEventListener('mousedown', this.canvasMouseDown);
      this.$refs.drawingCanvas.removeEventListener('mousemove', this.canvasMouseMove);
      this.$refs.drawingCanvas.removeEventListener('mouseleave', this.removeEraserIndicator);
    }
    window.removeEventListener('mouseup', this.canvasMouseUp);
    
    // Удаляем индикатор ластика, если он есть
    this.removeEraserIndicator();
    
    // Очищаем интервал таймера
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
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
        console.log('Загружены данные рисования с сервера:', this.drawingData.length, 'элементов');
        
        this.redrawCanvas(); // Перерисовываем холст с загруженными данными
        
        // Восстанавливаем состояние таймера после загрузки данных доски
        this.restoreTimerState();

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
      try {
        let response;
        if (taskToSave.id) {
          // Обновление существующей задачи
          response = await axios.patch(`/api/tasks/${taskToSave.id}/`, taskToSave, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          });
        } else {
          // Создание новой задачи
          response = await axios.post('/api/tasks/', {
            ...taskToSave,
            column: taskToSave.column // Убедимся, что column ID передается
          }, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          });
        }
        
        // Обновляем данные после успешного сохранения
        await this.fetchBoardData();
        this.closeModal();
      } catch (error) {
        console.error('Ошибка сохранения задачи:', error);
        alert('Не удалось сохранить задачу');
      }
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
      this.showDeleteConfirmation = true;
      this.columnToDelete = columnId;
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

      // Удаляем индикатор размера ластика при смене инструмента
      const existingIndicator = document.querySelector('.eraser-size-indicator');
      if (existingIndicator) {
        existingIndicator.remove();
      }

      // Удаляем предыдущие слушатели, чтобы избежать дублирования
      canvasEl.removeEventListener('mousedown', this.canvasMouseDown);
      canvasEl.removeEventListener('mousemove', this.canvasMouseMove);
      // mouseup слушаем на window, чтобы поймать отпускание кнопки даже вне холста
      window.removeEventListener('mouseup', this.canvasMouseUp); 

      if (toolName === 'pencil' || toolName === 'line' || toolName === 'eraser') {
        canvasEl.style.pointerEvents = 'auto';
        
        // Задаем курсор в зависимости от инструмента
        if (toolName === 'eraser') {
          // Используем простой CSS-курсор для ластика
          canvasEl.style.cursor = 'cell';
          
          // Также добавляем класс для возможности стилизации через CSS
          canvasEl.classList.add('eraser-cursor');
          canvasEl.classList.remove('pencil-cursor', 'line-cursor');
        } else if (toolName === 'pencil') {
          canvasEl.style.cursor = 'crosshair';
          canvasEl.classList.add('pencil-cursor');
          canvasEl.classList.remove('eraser-cursor', 'line-cursor');
        } else { // line
          canvasEl.style.cursor = 'crosshair';
          canvasEl.classList.add('line-cursor');
          canvasEl.classList.remove('eraser-cursor', 'pencil-cursor');
        }
        
        // Добавляем слушатели для рисования
        canvasEl.addEventListener('mousedown', this.canvasMouseDown);
        
        // Для ластика добавляем слушатель mousemove для отображения индикатора размера
        if (toolName === 'eraser') {
          canvasEl.addEventListener('mousemove', this.canvasMouseMove);
          
          // Добавляем обработчик для удаления индикатора при выходе мыши за пределы холста
          canvasEl.addEventListener('mouseleave', this.removeEraserIndicator);
        } else {
          // Убираем обработчик, если инструмент не ластик
          canvasEl.removeEventListener('mouseleave', this.removeEraserIndicator);
        }
        
        // mousemove и mouseup для рисования будут добавляться/удаляться динамически в mousedown/mouseup
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
      if (event.button !== 0) return; // Рисуем только левой кнопкой
      
      if (this.currentDrawingTool === 'pencil') {
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
      } else if (this.currentDrawingTool === 'eraser') {
        this.isDrawing = true;
        const { offsetX, offsetY } = event;
        
        // Размер ластика (фиксированный)
        const eraserSize = 20;
        
        // Запоминаем начальную точку стирания
        this.currentStroke = {
          type: 'eraser',
          points: [{ x: offsetX, y: offsetY }],
          size: eraserSize
        };
        
        // Визуально показываем процесс стирания - используем более заметный эффект
        this.drawingContext.save();
        this.drawingContext.globalCompositeOperation = 'destination-out';
        this.drawingContext.fillStyle = 'rgba(255, 255, 255, 1)';
        this.drawingContext.strokeStyle = 'rgba(255, 255, 255, 1)';
        
        // Используем круг для стирания
        this.drawingContext.beginPath();
        this.drawingContext.arc(offsetX, offsetY, eraserSize, 0, Math.PI * 2);
        this.drawingContext.fill();
        this.drawingContext.restore();
        
        this.$refs.drawingCanvas.addEventListener('mousemove', this.canvasMouseMove);
        window.addEventListener('mouseup', this.canvasMouseUp);
      }
    },
    canvasMouseMove(event) {
      const { offsetX, offsetY } = event;
      
      // Обновляем индикатор размера ластика, если это ластик
      if (this.currentDrawingTool === 'eraser') {
        this.updateEraserIndicator(offsetX, offsetY);
      }
      
      // Если не рисуем, просто выходим
      if (!this.isDrawing) return;
      
      if (this.currentDrawingTool === 'pencil' && this.currentStroke) {
        this.currentStroke.points.push({ x: offsetX, y: offsetY });

        // Продолжаем рисовать текущий путь
        this.drawingContext.lineTo(offsetX, offsetY);
        this.drawingContext.stroke();
      } else if (this.currentDrawingTool === 'eraser' && this.currentStroke) {
        this.currentStroke.points.push({ x: offsetX, y: offsetY });
        
        // Стираем часть рисунка с более четкими визуальными эффектами
        this.drawingContext.save();
        this.drawingContext.globalCompositeOperation = 'destination-out';
        this.drawingContext.fillStyle = 'rgba(255, 255, 255, 1)';
        this.drawingContext.strokeStyle = 'rgba(255, 255, 255, 1)';
        
        // Рисуем линию до предыдущей точки для непрерывного стирания
        if (this.currentStroke.points.length > 1) {
          const prevPoint = this.currentStroke.points[this.currentStroke.points.length - 2];
          
          // Рисуем толстую линию для стирания пути между точками
          this.drawingContext.lineWidth = this.currentStroke.size * 2;
          this.drawingContext.lineCap = 'round';
          this.drawingContext.lineJoin = 'round';
          
          this.drawingContext.beginPath();
          this.drawingContext.moveTo(prevPoint.x, prevPoint.y);
          this.drawingContext.lineTo(offsetX, offsetY);
          this.drawingContext.stroke();
        }
        
        // Рисуем круг в текущей позиции
        this.drawingContext.beginPath();
        this.drawingContext.arc(offsetX, offsetY, this.currentStroke.size, 0, Math.PI * 2);
        this.drawingContext.fill();
        
        this.drawingContext.restore();
        
        // Записываем время последнего движения ластика
        this.lastEraserMoveTime = Date.now();
        
        // Если с последнего применения изменений прошло более 1 секунды,
        // делаем промежуточное сохранение для улучшения отзывчивости
        if (!this.lastEraserSaveTime || (this.lastEraserMoveTime - this.lastEraserSaveTime > 1000)) {
          // Создаем новый массив без стёртых штрихов
          this.performIntermediateEraserSave();
        }
      }
    },
    
    // Метод для промежуточного сохранения при использовании ластика
    performIntermediateEraserSave() {
      if (!this.currentStroke || this.currentStroke.type !== 'eraser') return;
      
      const eraserSize = this.currentStroke.size || 20;
      const newDrawingData = [];
      let strokesModified = 0;
      
      // Обрабатываем каждый штрих
      this.drawingData.forEach(stroke => {
        // Пропускаем не карандашные штрихи, добавляем их без изменений
        if (stroke.type !== 'pencil') {
          newDrawingData.push(stroke);
          return;
        }
        
        // Для карандашных штрихов проверяем каждый сегмент
        const segments = [];
        let currentSegment = [];
        let inErasedArea = false;
        
        // Обрабатываем каждую точку штриха
        for (let i = 0; i < stroke.points.length; i++) {
          const point = stroke.points[i];
          
          // Проверяем, находится ли точка в зоне действия ластика
          const erased = this.currentStroke.points.some(eraserPoint => {
            const dx = point.x - eraserPoint.x;
            const dy = point.y - eraserPoint.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            return distance <= eraserSize;
          });
          
          // Если статус точки изменился (стёрта/не стёрта)
          if (erased !== inErasedArea) {
            // Если у нас есть незавершенный сегмент и мы переходим в зону стирания
            if (currentSegment.length > 0 && erased) {
              // Если у сегмента достаточно точек, добавляем его
              if (currentSegment.length > 1) {
                segments.push([...currentSegment]);
              }
              currentSegment = [];
            }
            
            // Обновляем флаг состояния
            inErasedArea = erased;
          }
          
          // Если точка не стёрта, добавляем её в текущий сегмент
          if (!erased) {
            currentSegment.push(point);
          }
        }
        
        // Добавляем последний сегмент, если он не пустой
        if (currentSegment.length > 1) {
          segments.push(currentSegment);
        }
        
        // Если мы разбили штрих на сегменты
        if (segments.length > 0) {
          // Создаем новые штрихи для каждого сегмента
          segments.forEach(segmentPoints => {
            if (segmentPoints.length >= 2) {
              newDrawingData.push({
                type: stroke.type,
                points: segmentPoints,
                color: stroke.color,
                lineWidth: stroke.lineWidth,
                lineCap: stroke.lineCap,
                lineJoin: stroke.lineJoin
              });
            }
          });
          
          strokesModified++;
        } else if (segments.length === 0 && !inErasedArea) {
          // Если штрих не изменился, добавляем оригинал
          newDrawingData.push(stroke);
        }
        // Если все сегменты были стерты, ничего не добавляем
      });
      
      // Если есть изменения, обновляем массив данных
      if (strokesModified > 0) {
        console.log(`Промежуточная модификация ${strokesModified} штрихов ластиком`);
        this.drawingData = newDrawingData;
        
        // Перерисовываем холст полностью, чтобы обновить отображение
        this.redrawCanvas();
        
        // Сохраняем только в localStorage для скорости
        try {
          const localDataKey = `board_${this.board.id}_drawing_data`;
          localStorage.setItem(localDataKey, JSON.stringify(this.drawingData));
        } catch (error) {
          console.warn('Ошибка при промежуточном сохранении:', error);
        }
      }
      
      // Обновляем время последнего сохранения
      this.lastEraserSaveTime = Date.now();
    },
    // Метод для обновления индикатора размера ластика
    updateEraserIndicator(x, y) {
      // Если инструмент не ластик, убираем индикатор и выходим
      if (this.currentDrawingTool !== 'eraser') {
        this.removeEraserIndicator();
        return;
      }
      
      // Ищем существующий индикатор
      let indicator = document.querySelector('.eraser-size-indicator');
      
      // Если его нет, создаем новый
      if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'eraser-size-indicator';
        document.body.appendChild(indicator);
      }
      
      // Получаем координаты холста относительно окна
      const canvas = this.$refs.drawingCanvas;
      if (!canvas) return;
      
      const rect = canvas.getBoundingClientRect();
      
      // Обновляем позицию индикатора
      indicator.style.left = `${rect.left + x}px`;
      indicator.style.top = `${rect.top + y}px`;
    },
    canvasMouseUp(event) {
      if (!this.isDrawing) return;
      if (event.button !== 0 && event.type === 'mouseup') return; 
      
      this.isDrawing = false;
      
      if (this.currentDrawingTool === 'pencil') {
        if (this.currentStroke && this.currentStroke.points.length > 1) {
          this.drawingData.push(this.currentStroke);
          console.log('Drawing data updated:', this.drawingData);
          this.saveDrawingData(); // Сохраняем данные на бэкенд
        }
      } else if (this.currentDrawingTool === 'eraser') {
        // Для ластика мы должны разделить или удалить штрихи, которые были стёрты
        if (this.currentStroke && this.currentStroke.points.length > 0) {
          // Используем тот же алгоритм, что и в performIntermediateEraserSave
          // но с сохранением на сервер в конце
          const eraserSize = this.currentStroke.size || 20;
          const newDrawingData = [];
          let strokesModified = 0;
          
          // Обрабатываем каждый штрих
          this.drawingData.forEach(stroke => {
            // Пропускаем не карандашные штрихи, добавляем их без изменений
            if (stroke.type !== 'pencil') {
              newDrawingData.push(stroke);
              return;
            }
            
            // Для карандашных штрихов проверяем каждый сегмент
            const segments = [];
            let currentSegment = [];
            let inErasedArea = false;
            
            // Обрабатываем каждую точку штриха
            for (let i = 0; i < stroke.points.length; i++) {
              const point = stroke.points[i];
              
              // Проверяем, находится ли точка в зоне действия ластика
              const erased = this.currentStroke.points.some(eraserPoint => {
                const dx = point.x - eraserPoint.x;
                const dy = point.y - eraserPoint.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                return distance <= eraserSize;
              });
              
              // Если статус точки изменился (стёрта/не стёрта)
              if (erased !== inErasedArea) {
                // Если у нас есть незавершенный сегмент и мы переходим в зону стирания
                if (currentSegment.length > 0 && erased) {
                  // Если у сегмента достаточно точек, добавляем его
                  if (currentSegment.length > 1) {
                    segments.push([...currentSegment]);
                  }
                  currentSegment = [];
                }
                
                // Обновляем флаг состояния
                inErasedArea = erased;
              }
              
              // Если точка не стёрта, добавляем её в текущий сегмент
              if (!erased) {
                currentSegment.push(point);
              }
            }
            
            // Добавляем последний сегмент, если он не пустой
            if (currentSegment.length > 1) {
              segments.push(currentSegment);
            }
            
            // Если мы разбили штрих на сегменты
            if (segments.length > 0) {
              // Создаем новые штрихи для каждого сегмента
              segments.forEach(segmentPoints => {
                if (segmentPoints.length >= 2) {
                  newDrawingData.push({
                    type: stroke.type,
                    points: segmentPoints,
                    color: stroke.color,
                    lineWidth: stroke.lineWidth,
                    lineCap: stroke.lineCap,
                    lineJoin: stroke.lineJoin
                  });
                }
              });
              
              strokesModified++;
            } else if (segments.length === 0 && !inErasedArea) {
              // Если штрих не изменился, добавляем оригинал
              newDrawingData.push(stroke);
            }
            // Если все сегменты были стерты, ничего не добавляем
          });
          
          // Обновляем drawingData и сохраняем изменения
          console.log(`Модифицировано ${strokesModified} штрихов, итоговое количество: ${newDrawingData.length}`);
          this.drawingData = newDrawingData;
          
          // Перерисовываем холст полностью, чтобы обновить отображение
          this.redrawCanvas();
          
          // Сохраняем обновленные данные на сервер
          this.saveDrawingData();
        }
      }
      
      this.currentStroke = null;
      
      this.$refs.drawingCanvas.removeEventListener('mousemove', this.canvasMouseMove);
      window.removeEventListener('mouseup', this.canvasMouseUp);
    },
    // --- End of Drawing implementation methods ---
    // --- Method to redraw canvas from drawingData ---
    redrawCanvas() {
      if (!this.drawingContext) return;
      // Очищаем холст
      this.drawingContext.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
      
      // Проверяем id доски
      if (!this.board || !this.board.id) {
        console.warn('Не удалось восстановить рисунок: ID доски не определен');
        return;
      }
      
      console.log('Восстанавливаем рисунок для доски ID:', this.board.id);
      console.log('Текущие данные рисования:', this.drawingData ? this.drawingData.length : 0, 'элементов');
      
      // Если данных нет на сервере или пустой массив, пробуем восстановить из localStorage
      try {
        const localDataKey = `board_${this.board.id}_drawing_data`;
        const localData = localStorage.getItem(localDataKey);
        
        if (localData) {
          const parsedData = JSON.parse(localData);
          
          // Проверяем, что это действительно массив
          if (parsedData && Array.isArray(parsedData)) {
            // Берем локальные данные только если:
            // 1. У нас вообще нет данных в памяти
            // 2. В localStorage массив не пустой И больше чем наш текущий
            if (!this.drawingData || 
                (parsedData.length > 0 && (!this.drawingData || parsedData.length > this.drawingData.length))) {
              console.log('Найдены данные в localStorage:', parsedData.length, 'элементов');
              this.drawingData = parsedData;
            }
          }
        }
      } catch (error) {
        console.warn('Ошибка при восстановлении из localStorage:', error);
      }
      
      // Инициализируем drawingData как пустой массив, если undefined
      if (!this.drawingData) {
        this.drawingData = [];
      }
      
      // Проверяем, есть ли вообще что рисовать
      if (this.drawingData.length === 0) {
        console.log('Нет данных для рисования, холст останется пустым');
        return; // Выходим, так как рисовать нечего
      }
      
      // Рисуем штрихи
      this.drawStrokes();
    },
    
    // Отдельный метод для рисования штрихов
    drawStrokes() {
      if (!Array.isArray(this.drawingData) || this.drawingData.length === 0) {
        return;
      }
      
      // Сначала сортируем штрихи, чтобы они рисовались в правильном порядке
      // (новые поверх старых)
      const sortedStrokes = [...this.drawingData];
      
      // Рисуем каждый штрих
      sortedStrokes.forEach(stroke => {
        if (stroke.type === 'pencil' && stroke.points && stroke.points.length >= 2) {
          // Применяем все стили штриха
          this.drawingContext.save();
          
          this.drawingContext.beginPath();
          this.drawingContext.moveTo(stroke.points[0].x, stroke.points[0].y);
          
          this.drawingContext.strokeStyle = stroke.color || 'black';
          this.drawingContext.lineWidth = stroke.lineWidth || 2;
          this.drawingContext.lineCap = stroke.lineCap || 'round';
          this.drawingContext.lineJoin = stroke.lineJoin || 'round';

          // Рисуем линии между всеми точками
          for (let i = 1; i < stroke.points.length; i++) {
            this.drawingContext.lineTo(stroke.points[i].x, stroke.points[i].y);
          }
          
          this.drawingContext.stroke();
          this.drawingContext.restore();
        }
        // В будущем здесь будут другие типы: line, rectangle и т.д.
      });
    },
    // --- End of redraw method ---
    // --- Method to save drawing data to backend ---
    async saveDrawingData() {
      if (!this.board || !this.board.id) {
        console.error('Не удалось сохранить рисунок: ID доски не определен');
        return;
      }
      
      // Если нет данных для сохранения, создаем пустой массив вместо выхода
      // чтобы очистить рисунок, если все элементы были стерты
      if (!this.drawingData || !Array.isArray(this.drawingData)) {
        console.log('Инициализация пустого массива данных рисования');
        this.drawingData = [];
      }
      
      console.log('Сохраняем рисунок для доски ID:', this.board.id, 'элементов:', this.drawingData.length);
      
      // Сначала сохраняем в localStorage для надежности
      try {
        const localDataKey = `board_${this.board.id}_drawing_data`;
        localStorage.setItem(localDataKey, JSON.stringify(this.drawingData));
        console.log('Данные рисунка сохранены в localStorage');
      } catch (localStorageError) {
        console.warn('Ошибка сохранения в localStorage:', localStorageError);
      }
      
      // Затем отправляем на сервер
      try {
        await axios.patch(`/api/boards/${this.board.id}/`, {
          drawing_data: this.drawingData
        }, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        console.log('Данные рисунка сохранены на сервере');
      } catch (error) {
        console.error('Ошибка сохранения на сервере:', error.response ? error.response.data : error.message);
        // Если сохранение на сервере не удалось, пробуем повторить через 5 секунд
        setTimeout(() => {
          console.log('Повторная попытка сохранения рисунка...');
          this.saveDrawingData();
        }, 5000);
      }
    },
    // --- End of save drawing data method ---
    // Новые методы для подтверждения и отмены удаления колонки
    confirmDeleteColumn() {
      const columnIndex = this.board.columns.findIndex(c => c.id === this.columnToDelete);
      if (columnIndex !== -1) {
        this.deleteColumn(columnIndex);
      }
      this.resetDeleteConfirmation();
    },
    
    cancelDeleteColumn() {
      this.resetDeleteConfirmation();
    },
    
    resetDeleteConfirmation() {
      this.showDeleteConfirmation = false;
      this.columnToDelete = null;
    },
    openTimerSettings() {
      this.showTimerSettings = true;
    },
    closeTimerSettings() {
      this.showTimerSettings = false;
    },
    startTimer() {
      // Проверка на корректность введенных значений
      this.timerHours = Math.max(0, Math.min(23, this.timerHours || 0));
      this.timerMinutes = Math.max(0, Math.min(59, this.timerMinutes || 0));
      this.timerSeconds = Math.max(0, Math.min(59, this.timerSeconds || 0));
      
      // Проверяем, что хотя бы одно значение больше нуля
      if (this.timerHours === 0 && this.timerMinutes === 0 && this.timerSeconds === 0) {
        // По умолчанию устанавливаем 5 минут
        this.timerMinutes = 5;
      }
      
      // Если название не задано, устанавливаем значение по умолчанию
      if (!this.timerName.trim()) {
        this.timerName = 'Задача';
      }
      
      this.showTimerSettings = false;
      this.timerActive = true;
      this.timerRemaining = this.timerHours * 3600 + this.timerMinutes * 60 + this.timerSeconds;
      
      // Сохраняем время начала для восстановления таймера при обновлении
      const timerEndTime = Date.now() + (this.timerRemaining * 1000);
      
      console.log('Запуск таймера:', {
        name: this.timerName,
        hours: this.timerHours,
        minutes: this.timerMinutes,
        seconds: this.timerSeconds,
        totalSeconds: this.timerRemaining,
        endTime: new Date(timerEndTime).toLocaleTimeString()
      });
      
      // Сначала сохраняем состояние перед запуском
      this.saveTimerState(timerEndTime);
      
      // Очищаем предыдущий интервал если он есть
      if (this.timerInterval) {
        clearInterval(this.timerInterval);
        this.timerInterval = null;
      }
      
      this.timerInterval = setInterval(() => {
        this.timerRemaining--;
        
        // Периодически (каждые 5 секунд) обновляем состояние в localStorage
        // для учета возможных системных задержек
        if (this.timerRemaining % 5 === 0) {
          const updatedEndTime = Date.now() + (this.timerRemaining * 1000);
          this.saveTimerState(updatedEndTime);
        }
        
        if (this.timerRemaining <= 0) {
          this.timerActive = false;
          this.showTimerEndDialog = true;
          clearInterval(this.timerInterval);
          this.timerInterval = null;
          // Очищаем данные таймера при его завершении
          this.clearTimerState();
        }
      }, 1000);
    },
    handleTimerStart(timerSettings) {
      this.timerName = timerSettings.name;
      this.timerHours = timerSettings.hours;
      this.timerMinutes = timerSettings.minutes;
      this.timerSeconds = timerSettings.seconds;
      this.startTimer();
    },
    stopTimer() {
      this.timerActive = false;
      clearInterval(this.timerInterval);
      // Очищаем данные таймера при его остановке
      this.clearTimerState();
    },
    // Сохраняем состояние таймера в localStorage
    saveTimerState(endTime) {
      if (!this.board || !this.board.id) {
        console.log('ID доски не найден, невозможно сохранить таймер');
        return;
      }
      
      try {
        localStorage.setItem(`timer_${this.board.id}_active`, this.timerActive);
        localStorage.setItem(`timer_${this.board.id}_name`, this.timerName);
        localStorage.setItem(`timer_${this.board.id}_end_time`, endTime);
        
        console.log('Состояние таймера сохранено:', {
          boardId: this.board.id,
          active: this.timerActive,
          name: this.timerName,
          endTime: new Date(parseInt(endTime)).toLocaleTimeString()
        });
      } catch (error) {
        console.error('Ошибка при сохранении таймера в localStorage:', error);
      }
    },
    
    // Восстанавливаем состояние таймера из localStorage
    restoreTimerState() {
      if (!this.board || !this.board.id) {
        console.log('ID доски не найден, невозможно восстановить таймер');
        return;
      }
      
      console.log('Восстановление таймера для доски:', this.board.id);
      
      const isActive = localStorage.getItem(`timer_${this.board.id}_active`);
      const timerName = localStorage.getItem(`timer_${this.board.id}_name`);
      const endTime = localStorage.getItem(`timer_${this.board.id}_end_time`);
      
      console.log('Данные таймера из localStorage:', { isActive, timerName, endTime });
      
      if (isActive === 'true' && endTime) {
        const remainingMs = parseInt(endTime) - Date.now();
        console.log('Оставшееся время (мс):', remainingMs);
        
        if (remainingMs > 0) {
          this.timerActive = true;
          this.timerName = timerName || 'Задача';
          this.timerRemaining = Math.floor(remainingMs / 1000);
          
          console.log('Таймер восстановлен:', { 
            name: this.timerName, 
            remainingSeconds: this.timerRemaining 
          });
          
          // Очищаем предыдущий интервал если он есть
          if (this.timerInterval) {
            clearInterval(this.timerInterval);
          }
          
          this.timerInterval = setInterval(() => {
            this.timerRemaining--;
            if (this.timerRemaining <= 0) {
              this.timerActive = false;
              this.showTimerEndDialog = true;
              clearInterval(this.timerInterval);
              this.timerInterval = null;
              this.clearTimerState();
            }
          }, 1000);
        } else {
          // Если таймер должен был закончиться во время отсутствия пользователя
          console.log('Таймер устарел, очищаем данные');
          this.clearTimerState();
        }
      } else {
        console.log('Нет активного таймера для восстановления');
      }
    },
    // Очищаем данные таймера в localStorage
    clearTimerState() {
      if (!this.board || !this.board.id) {
        console.log('ID доски не найден, невозможно очистить данные таймера');
        return;
      }
      
      try {
        localStorage.removeItem(`timer_${this.board.id}_active`);
        localStorage.removeItem(`timer_${this.board.id}_name`);
        localStorage.removeItem(`timer_${this.board.id}_end_time`);
        console.log('Данные таймера очищены для доски:', this.board.id);
      } catch (error) {
        console.error('Ошибка при очистке данных таймера:', error);
      }
    },
    formatTime(seconds) {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const remainingSeconds = seconds % 60;
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    },
    // Обработчик клавиш для быстрого выбора инструментов
    handleKeyDown(event) {
      // Если фокус на input или textarea, не обрабатываем клавиши
      if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
      }
      
      switch (event.key.toLowerCase()) {
        case 'v': // Курсор
          this.handleToolSelected('cursor');
          break;
        case 'p': // Карандаш
          this.handleToolSelected('pencil');
          break;
        case 'l': // Линия
          this.handleToolSelected('line');
          break;
        case 'e': // Ластик
          this.handleToolSelected('eraser');
          break;
      }
    },
    // Метод для удаления индикатора ластика
    removeEraserIndicator() {
      const existingIndicator = document.querySelector('.eraser-size-indicator');
      if (existingIndicator) {
        existingIndicator.remove();
      }
    },
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
  justify-content: space-between; /* Распределяем элементы равномерно */
}

.menu-placeholder {
  width: 50px; /* Место для кнопки меню */
}

.board-title {
  font-size: 1.8em;
  font-weight: 600;
  color: #2c3e50;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 8px;
  transition: background-color 0.2s ease;
  text-align: left;
  flex-shrink: 0;
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-left: 35px; /* Добавляем отступ, чтобы название не перекрывалось кнопкой сайдбара */
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
  flex-shrink: 0;
  max-width: 300px;
}

.header-buttons {
  display: flex;
  gap: 15px; /* Отступы между кнопками */
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

.fixed-columns-container {
  position: fixed;
  top: 120px; /* Отступ сверху */
  left: 20px; /* Небольшой отступ слева */
  z-index: 1000;
  /* Удаляем display: flex, чтобы колонки не зависели друг от друга */
  display: block;
  background: transparent;
  pointer-events: auto; /* Разрешаем события, чтобы затемнение влияло на фиксированные колонки */
}

/* Добавляем стили для расположения колонок по горизонтали, но независимо друг от друга */
.fixed-columns-container :deep(.column):nth-child(1) {
  position: fixed;
  top: 120px;
  left: 20px;
}

.fixed-columns-container :deep(.column):nth-child(2) {
  position: fixed;
  top: 120px;
  left: 340px; /* 20px + 300px (ширина колонки) + 20px (отступ) */
}

.fixed-columns-container :deep(.column):nth-child(3) {
  position: fixed;
  top: 120px;
  left: 660px; /* 20px + 300px + 20px + 300px + 20px */
}

/* Гарантируем, что у фиксированных колонок всегда будут видны цветные полоски */
.fixed-columns-container :deep(.column) {
  border-top-width: 0 !important;
  background-color: white !important; /* Принудительно белый фон */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important; /* Более мягкая тень */
}

.fixed-columns-container :deep(.column) .color-stripe {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 10px !important;
  z-index: 9999 !important;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  border-radius: 12px 12px 0 0 !important;
}

.timer-container {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-grow: 1;
}

.timer-display {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid #e1e4e8;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  color: #4a5568;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  min-width: 180px;
  justify-content: center;
  z-index: 50;
  font-family: 'Poppins', 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.3px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.timer-display:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.95);
}

.timer-display i {
  color: #5b9cff;
  font-size: 18px;
}

.timer-display span {
  font-weight: 500;
  font-family: 'Poppins', 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

.timer-display.timer-active {
  background: rgba(255, 235, 235, 0.95);
  border: 1px solid rgba(235, 90, 70, 0.3);
  box-shadow: 0 2px 8px rgba(235, 90, 70, 0.2);
  font-family: 'Poppins', 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.3px;
}

.timer-display.timer-active i {
  color: #eb5a46;
}

.timer-display.timer-active .stop-icon {
  margin-left: 8px;
  color: #eb5a46;
  font-size: 16px;
}

.timer-display.timer-active:hover {
  background: rgba(255, 230, 230, 0.98);
  box-shadow: 0 4px 12px rgba(235, 90, 70, 0.3);
  transform: translateY(-2px);
}

.timer-settings {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
  position: absolute;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 15px;
  min-width: 300px;
}

.timer-name-input {
  padding: 12px;
  border: 1px solid #e1e4e8;
  border-radius: 8px;
  font-size: 15px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  width: 100%;
  transition: all 0.3s ease;
}

.timer-name-input:focus {
  border-color: #5b9cff;
  box-shadow: 0 0 0 3px rgba(91, 156, 255, 0.2);
  outline: none;
}

.timer-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.timer-input {
  width: 60px;
  padding: 12px;
  text-align: center;
  border: 1px solid #e1e4e8;
  border-radius: 8px;
  font-size: 18px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
}

.timer-input:focus {
  border-color: #5b9cff;
  box-shadow: 0 0 0 3px rgba(91, 156, 255, 0.2);
  outline: none;
}

.timer-separator {
  font-size: 20px;
  font-weight: bold;
  color: #4a5568;
}

.timer-buttons {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.timer-button {
  padding: 10px 18px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(240, 242, 245, 0.8);
  color: #4a5568;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.timer-button:hover {
  background: rgba(230, 232, 235, 0.9);
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
}

.start-timer {
  background: rgba(91, 156, 255, 0.9);
  color: white;
  box-shadow: 0 2px 8px rgba(91, 156, 255, 0.3);
}

.start-timer:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91, 156, 255, 0.4);
}

.cancel-timer {
  background: rgba(240, 242, 245, 0.8);
  color: #4a5568;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.cancel-timer:hover {
  background: rgba(230, 232, 235, 0.9);
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
}

/* Стили для курсоров рисования */
.eraser-cursor {
  /* Используем простой и понятный курсор */
  cursor: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAFEmlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDE5LTAxLTE3VDEzOjQwOjIyKzAzOjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAxOS0wMS0xN1QxMzo0MTowNSswMzowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAxOS0wMS0xN1QxMzo0MTowNSswMzowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo0YjZmYzQ4NC1iMDRlLTE3NGItOWRkMC0zZjRkZTkwZmYxNmQiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6NGI2ZmM0ODQtYjA0ZS0xNzRiLTlkZDAtM2Y0ZGU5MGZmMTZkIiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6NGI2ZmM0ODQtYjA0ZS0xNzRiLTlkZDAtM2Y0ZGU5MGZmMTZkIj4gPHhtcE1NOkhpc3Rvcnk+IDxyZGY6U2VxPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iY3JlYXRlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo0YjZmYzQ4NC1iMDRlLTE3NGItOWRkMC0zZjRkZTkwZmYxNmQiIHN0RXZ0OndoZW49IjIwMTktMDEtMTdUMTM6NDA6MjIrMDM6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCBDQyAyMDE5IChXaW5kb3dzKSIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7h/gS1AAADrElEQVRYw7WXS2wbVRSG/3Nn7IydOHFjJ06cprHrhKRWpJJupkVFTVUhQGJFi5AQSEgIJBYI2CAWLLoBJHZI7GDJAoGQumFFQYhNVaSKdFG1aWpM4iR+xvE7tuMZz4PLIggpbew0mnOWo3vv+c53z3/PuUcyDIM+uTfc9wghBEII8vm8/d3z02oWj2/qAWg9gFQqPe6xPUKrlCNalqUahmEkhPzSK5afAkB7BKYrK1+7P/9oRpmahDIxCUmW6f7VZaxcvkTN7c3XnklfT3f5NQsghPh9cHD8nV/vLEQnJnbszz9E8tPzOLBSg/W51/HAw0ef6grgWQQc56jHVxz86KcbN3uXVmr5+iGl5eRnF5DsPvnmkcHC+d0ArLsBFIvF5+12++sXv7qED8+9jfj9pJnLFzCZ2kF3zYuTJ579bNkSl/N5oaurC7zT2XVqXa/JZrPH/X7/hxeufPf48MR0jKqyjO1MFryvD7zqx/ZWGmuRGxPtdvfCO2++/nZ8fBQz01MoFArY3NpOX7t+4/2tyMqZcDgcHRgYQCAQ2PMRTE5OHpQ1rZW8n8DJ4yforKYhvx2D3G5jdnEB7XoNoUMHceToUbQaNQSDIciUQlVl5W//1tZiuVwK2Wwe+Xyxx0uopVKpZi6Xg9VqpXfu3qNMw0A+m4Pd4YBECNQ+P9rtFrrdLkhqH3i7A4l4HJFIBP3+AKZSW7BYrFIqtfX7pUuXPioUCpibm+sNwOPxaG632+dwOFAsFmG1WtFutyFLFEo2D93QUSqVQO126LoOSZZRqVSRiMehKDJUVUW5XEYsFnvV6/W+FAwGfw4Gg9je3sZuRuQRABQALBYLOOfQdR0URUH34QO7bDbDbDbjwYMkzGYKTdMgyzJsNhu4rgMA9ECATCaT4Zz/ZRuN5nciEYG/34+eAMrlcuR2NLaUzRWQzxf+SZDKvwXoukCu8CficZGwmA0IIcAYA2MdAMDQyCFZcXn9hmCk8/CL4+OjrUPj45f9fj8GBgZ6ADiOw7cTiRi1WK+Ojo6UvvjqMnPqYH1eO54GYwkgV9OV0tPJWIyaZQlCSIyPj8cPDAWTHMejPTUiABCPxyEYbzqdzmdaLb0WbzCNc47NrQy4EFBVFQMDg7BZLXxlZeU3znnoQCBwu+fJqKoq3G43Wko6vXHnbtrtcqJSrUKSJQQCAYRCIbAsK1GUrmez2VMAsNeLqK9QKKBarc4vLi6eb7Va4JyDMRYhhHzPGHuh95/yXwa8Ic/6R1V9AAAAAElFTkSuQmCC') 12 12, cell !important;
}

/* При необходимости можно добавить стили для других инструментов */
.pencil-cursor {
  cursor: crosshair !important;
}

.line-cursor {
  cursor: crosshair !important;
}

/* Индикатор размера ластика */
.eraser-size-indicator {
  position: absolute;
  border: 2px dashed rgba(255, 0, 0, 0.6);
  background: rgba(255, 0, 0, 0.1);
  border-radius: 50%;
  pointer-events: none;
  transform: translate(-50%, -50%);
  z-index: 1000;
  width: 40px !important;
  height: 40px !important;
  box-shadow: 0 0 0 1px white;
}
</style>