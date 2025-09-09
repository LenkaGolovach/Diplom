<template>
  <div 
    class="column"
    :class="{ 'column-collapsed': isCollapsed && isFixedPosition }"
    :style="columnStyle"
    @mousedown.left="startDrag"
  >
    <div 
      class="color-stripe column-drag-handle"
      :style="{ backgroundColor: column.color }"
    >
    </div>
    <div 
      class="column-header" 
      @click="isFixedPosition && toggleCollapse()"
      :class="{ 'clickable': isFixedPosition }"
    >
      <div
        v-if="!isEditing"
        class="column-title"
        @dblclick.prevent="startEditing"
      >
        {{ column.name }}
      </div>
      <input
        v-else
        ref="titleInput"
        v-model="newName"
        @blur="stopEditing"
        @keyup.enter="stopEditing"
        class="column-title-input"
        @mousedown.stop
      />
      <button @click.prevent.stop="deleteColumnHandler" class="delete-column-button" @mousedown.stop>×</button>
    </div>
    
    <div class="column-content" v-show="!isCollapsed || !isFixedPosition">
      <draggable
        v-model="tasks"
        group="tasks"
        class="tasks"
        item-key="id"
        handle=".task-drag-handle"
        @change="onTaskChange"
        @mousedown.native.stop
      >
        <template #item="{ element }">
          <Task 
            :task="element" 
            @click="openTaskModalHandler(element)"
            @delete.stop="deleteTaskHandler(element)"
          />
        </template>
      </draggable>

      <button 
        v-if="!showTaskForm" 
        class="add-task-button" 
        @click.prevent.stop="showTaskForm = true"
        @mousedown.stop
      >
        + Добавить задачу
      </button>
      
      <div v-if="showTaskForm" class="new-task-form" @mousedown.stop>
        <input 
          ref="newTaskInput"
          v-model="newTaskName"
          class="new-task-input"
          placeholder="Введите название задачи"
          @keyup.enter="createTaskHandler"
        />
        <div class="new-task-actions">
          <button @click.prevent.stop="createTaskHandler" class="save-task-button">Сохранить</button>
          <button @click.prevent.stop="cancelTaskCreation" class="cancel-task-button">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Task from './Task.vue';
import draggable from 'vuedraggable';
import axios from 'axios';
import { ref } from 'vue';

export default {
  components: {
    Task,
    draggable,
  },
  props: {
    column: {
      type: Object,
      required: true,
    },
    isFixedPosition: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      tasks: Array.isArray(this.column.tasks) ? [...this.column.tasks] : [],
      isEditing: false,
      showTaskForm: false,
      newTaskName: '',
      newName: this.column.name,
      dragging: false,
      dragOffsetX: 0,
      dragOffsetY: 0,
      isCollapsed: false
    };
  },
  computed: {
    columnStyle() {
      if (this.isFixedPosition) {
        return {
          zIndex: this.column.zIndex || 0,
          // Если это фиксированная колонка, то не задаем position
        };
      }
      return {
        left: `${this.column.x || 0}px`,
        top: `${this.column.y || 0}px`,
        zIndex: this.column.zIndex || 0,
        position: 'absolute',
      };
    },
  },
  methods: {
    toggleCollapse() {
      if (this.isFixedPosition) {
        this.isCollapsed = !this.isCollapsed;
      }
    },
    startDrag(event) {
      if (this.isFixedPosition) return; // Не перемещаем фиксированные колонки
      
      this.dragging = true;
      this.dragOffsetX = event.clientX - this.column.x;
      this.dragOffsetY = event.clientY - this.column.y;

      this.$emit('bring-to-front', this.column.id);

      document.addEventListener('mousemove', this.onDrag);
      document.addEventListener('mouseup', this.stopDrag);
    },
    onDrag(event) {
      if (!this.dragging) return;
      
      let newX = event.clientX - this.dragOffsetX;
      let newY = event.clientY - this.dragOffsetY;

      this.$el.style.left = `${newX}px`;
      this.$el.style.top = `${newY}px`;
    },
    stopDrag() {
      if (!this.dragging) return;
      this.dragging = false;
      document.removeEventListener('mousemove', this.onDrag);
      document.removeEventListener('mouseup', this.stopDrag);

      const finalX = parseInt(this.$el.style.left, 10);
      const finalY = parseInt(this.$el.style.top, 10);

      const updatedColumn = {
        ...this.column,
        x: finalX,
        y: finalY,
      };
      this.$emit('save-column-position', updatedColumn);
    },
    startEditing() {
      this.isEditing = true;
      this.$nextTick(() => {
        this.$refs.titleInput.focus();
      });
    },
    stopEditing() {
      this.isEditing = false;
      this.updateColumnHandler();
    },
    updateColumnHandler() {
      this.$emit('update-column', { ...this.column, name: this.newName });
    },
    deleteColumnHandler() {
      this.$emit('delete-column');
    },
    onTaskChange(event) {
      console.log('Draggable change event:', event);
      const movedTask = event.moved ? event.moved.element : null;
      const addedTask = event.added ? event.added.element : null;
      const removedTask = event.removed ? event.removed.element : null;

      this.$emit('update-tasks', this.tasks); 

      this.tasks.forEach((task, index) => {
         if (task.order !== index || (addedTask && task.id === addedTask.id)) { 
           this.updateTaskOrder(task, index);
         }
      });
    },
    async updateTaskOrder(task, newOrder) {
        console.log(`Updating task ${task.id} in column ${this.column.id} to order ${newOrder}. Task data:`, JSON.parse(JSON.stringify(task)));
        try {
            await axios.patch(`/api/tasks/${task.id}/`, {
                name: task.name,
                column: this.column.id,
                order: newOrder
            }, {
                headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
            });
            console.log(`Task ${task.id} successfully updated on server. New order: ${newOrder}, new column: ${this.column.id}`);
            task.order = newOrder;
            task.column = this.column.id;
        } catch (error) {
            console.error(`Ошибка обновления порядка для задачи ${task.id}:`, error);
            if (error.response) {
                console.error("Server response:", error.response.data);
            }
        }
    },
    createTaskHandler() {
      if (!this.newTaskName.trim()) {
        this.$nextTick(() => {
          this.$refs.newTaskInput.focus();
        });
        return;
      }
      
      this.$emit('add-task', this.newTaskName.trim());
      this.newTaskName = '';
      this.showTaskForm = false;
    },
    cancelTaskCreation() {
      this.newTaskName = '';
      this.showTaskForm = false;
    },
    openTaskModalHandler(task) {
      this.$emit('openTaskModal', task);
    },
    deleteTaskHandler(task) {
      const index = this.tasks.findIndex(t => t.id === task.id);
      if (index !== -1) {
        axios.delete(`/api/tasks/${task.id}/`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        }).then(() => {
          this.tasks.splice(index, 1);
          this.$emit('update-tasks', this.tasks); 
        }).catch(error => {
          console.error('Ошибка удаления задачи:', error);
        });
      }
    },
  },
  watch: {
    showTaskForm(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          this.$refs.newTaskInput.focus();
        });
      }
    },
    'column.name'(newName) {
        this.newName = newName;
    },
    'column.tasks': {
      handler(newTasks) {
        if (JSON.stringify(this.tasks) !== JSON.stringify(newTasks)) {
            this.tasks = Array.isArray(newTasks) ? [...newTasks] : [];
        }
      },
      deep: true,
      immediate: true
    }
  }
};
</script>

<style scoped>
/* Убираем все стили для fixed-column, так как они не нужны */
.fixed-column {
  /* пусто */
}

.column {
  background-color: #f8f9fa;
  border-radius: 12px;
  padding: 0;
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  /* Высота определяется только содержимым */
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  cursor: grab;
  user-select: none;
  height: auto; /* Принудительно устанавливаем auto height */
  transition: transform 0.1s ease; /* Уменьшаем задержку при перемещении */
}

.column-collapsed {
  height: auto !important; /* Показываем только заголовок и полоску */
  max-height: 52px !important;
  overflow: hidden;
  padding-bottom: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: max-height 0.2s ease;
}

/* Убедимся, что цветная полоска всегда видна у свернутых колонок */
.column-collapsed .color-stripe {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.column:active {
  cursor: grabbing;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.color-stripe {
  height: 10px;
  border-radius: 12px 12px 0 0;
  margin-bottom: 10px;
  display: block !important; /* Гарантируем, что полоска всегда отображается */
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 10;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  margin-top: 15px; /* Добавляем отступ для полоски сверху */
}

.column-header.clickable {
  cursor: pointer;
  position: relative;
}

/* Индикатор сворачивания */
.column-header.clickable::after {
  content: '⌄';
  position: absolute;
  right: 40px;
  font-size: 20px;
  transition: transform 0.3s ease;
  opacity: 0.5;
}

.column-collapsed .column-header.clickable::after {
  transform: rotate(180deg);
}

.column-content {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  opacity: 1;
  transition: opacity 0.2s ease;
  height: auto;
}

.column-collapsed .column-content {
  opacity: 0;
}

.column-title {
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  color: #2c3e50;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.3px;
  transition: all 0.2s ease;
}

.column-title:hover {
  background: rgba(0, 0, 0, 0.05);
}

.column-title-input {
  font-weight: 600;
  font-size: 16px;
  width: 100%;
  padding: 8px 10px;
  border: 2px solid #5a9bd4;
  border-radius: 6px;
  outline: none;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  box-shadow: 0 0 0 3px rgba(90, 155, 212, 0.2);
}

.delete-column-button {
  background: none;
  border: none;
  color: #95a5a6;
  font-size: 22px;
  cursor: pointer;
  padding: 4px;
  margin-left: 8px;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.delete-column-button:hover {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
  transform: rotate(90deg);
}

.tasks {
  padding: 0 10px 10px 10px;
  overflow-y: auto;
  flex-grow: 1;
  min-height: 60px;
}

.tasks::-webkit-scrollbar {
  width: 6px;
}

.tasks::-webkit-scrollbar-thumb {
  background-color: #ccc;
  border-radius: 3px;
}

.tasks::-webkit-scrollbar-track {
  background-color: transparent;
}

.add-task-button {
  width: 100%;
  padding: 12px 10px;
  border: none;
  background: rgba(91, 156, 255, 0.08);
  color: #5b9cff;
  cursor: pointer;
  border-radius: 8px;
  margin-top: 12px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
  letter-spacing: 0.3px;
  font-size: 14px;
}

.add-task-button:hover {
  background: rgba(91, 156, 255, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(91, 156, 255, 0.1);
}

.new-task-form {
  margin-top: 12px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
  width: 90%;
  max-width: 250px;
  margin-left: auto;
  margin-right: auto;
}

.new-task-input {
  width: 100%;
  padding: 10px 1px;
  border: 1px solid #bdc3c7;
  border-radius: 8px;
  outline: none;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 14px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.new-task-input:focus {
  border-color: #5a9bd4;
  box-shadow: 0 0 0 2px rgba(90, 155, 212, 0.2);
}

.new-task-actions {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
}

.save-task-button {
  background: rgba(91, 156, 255, 0.08);
  border: none;
  color: #5b9cff;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
}

.save-task-button:hover {
  background: rgba(91, 156, 255, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(91, 156, 255, 0.1);
}

.cancel-task-button {
  background: none;
  border: none;
  color: #95a5a6;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
}

.cancel-task-button:hover {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
}

.column-collapsed .color-stripe {
  height: 10px;
  border-radius: 12px 12px 0 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* Усиление цветной полоски для фиксированных колонок */
.column[class*='is-fixed-position'] .color-stripe {
  height: 10px;
  filter: saturate(1.2);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Убедимся, что цветная полоска видна у фиксированных колонок */
.column[class*='is-fixed-position'] .color-stripe {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 2;
}
</style>