<template>
  <div class="column">
    <div 
      class="color-stripe"
      :style="{ backgroundColor: column.color }"
    ></div>
    <div class="column-header">
      <div
        v-if="!isEditing"
        class="column-title"
        @dblclick="startEditing"
      >
        {{ column.name }}
      </div>
      <input
        v-else
        ref="titleInput"
        v-model="column.name"
        @blur="stopEditing"
        @keyup.enter="stopEditing"
        class="column-title-input"
      />
      <button class="delete-column-button" @click="deleteColumn">
        ×
      </button>
    </div>
    
    <draggable
      v-model="tasks"
      group="tasks"
      class="tasks"
      item-key="id"
      @change="onTaskChange"
    >
      <template #item="{ element }">
        <Task 
          :task="element" 
          @click="$emit('openTaskModal', element)"
          @delete="deleteTask(element)"
        />
      </template>
    </draggable>

    <button 
      v-if="!showTaskForm" 
      class="add-task-button" 
      @click="showTaskForm = true"
    >
      + Добавить задачу
    </button>
    
    <div v-if="showTaskForm" class="new-task-form">
      <input 
        ref="newTaskInput"
        v-model="newTaskName"
        class="new-task-input"
        placeholder="Введите название задачи"
        @keyup.enter="createTask"
      />
      <div class="new-task-actions">
        <button @click="createTask" class="save-task-button">Сохранить</button>
        <button @click="cancelTaskCreation" class="cancel-task-button">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script>
import Task from './Task.vue';
import draggable from 'vuedraggable';
import axios from 'axios';

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
  },
  data() {
    return {
      tasks: this.column.tasks,
      isEditing: false,
      showTaskForm: false,
      newTaskName: '',
    };
  },
  methods: {
    startEditing() {
      this.isEditing = true;
      this.$nextTick(() => {
        this.$refs.titleInput.focus();
      });
    },
    stopEditing() {
      this.isEditing = false;
      this.$emit('update-column', this.column);
    },
    addTask() {
      this.$emit('add-task');
    },
    deleteColumn() {
      this.$emit('delete-column');
    },
    async deleteTask(task) {
      try {
        await axios.delete(`/api/tasks/${task.id}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        
        // Удаляем задачу из локального состояния
        const index = this.tasks.findIndex(t => t.id === task.id);
        if (index !== -1) {
          this.tasks.splice(index, 1);
        }
      } catch (error) {
        console.error('Ошибка удаления:', error);
      }
    },
    async onTaskChange(event) {
      // Если задача была перемещена из одной колонки в другую
      if (event.added) {
        const task = event.added.element;
        try {
          const newOrder = this.tasks.length - 1;
          
          await axios.patch(`/api/tasks/${task.id}/`, {
            column: this.column.id,
            order: newOrder
          }, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });
          
          this.$emit('update-tasks', this.tasks);
        } catch (error) {
          console.error('Ошибка добавления задачи в колонку:', error);
        }
      }
      // Если задача была перемещена внутри колонки
      else if (event.moved) {
        const task = event.moved.element;
        try {
          await axios.patch(`/api/tasks/${task.id}/`, {
            column: this.column.id,
            order: event.moved.newIndex
          }, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });
          this.$emit('update-tasks', this.tasks);
        } catch (error) {
          console.error('Ошибка перемещения задачи:', error);
        }
      }
      
      // Если задача была добавлена из другой колонки
      if (event.added) {
        const task = event.added.element;
        try {
          await axios.patch(`/api/tasks/${task.id}/`, {
            column: this.column.id,
            order: event.added.newIndex
          }, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });
          this.$emit('update-tasks', this.tasks);
        } catch (error) {
          console.error('Ошибка добавления задачи в колонку:', error);
          this.tasks = this.tasks.slice().reverse();
        }
      }
    },
    createTask() {
      if (!this.newTaskName.trim()) {
        // Если имя пустое, сфокусируемся на поле ввода
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
  },
  watch: {
    showTaskForm(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          this.$refs.newTaskInput.focus();
        });
      }
    }
  },
};
</script>

<style scoped>
.column {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 12px;
  width: 300px;
  min-width: 300px;
  max-width: 350px;
  margin: 0;
  padding: 16px;
  position: relative;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 160px);
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  flex-grow: 1;
}

.column:hover {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.color-stripe {
  height: 5px;
  border-radius: 10px 10px 0 0;
  margin: -16px -16px 16px -16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.column-title {
  font-weight: 600;
  font-size: 16px;
  padding: 8px 10px;
  cursor: pointer;
  border-radius: 6px;
  flex: 1;
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
  flex: 1;
  overflow-y: auto;
  min-height: 40px;
  padding: 5px 0;
  margin: 0 -5px;
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
}

.tasks::-webkit-scrollbar {
  width: 5px;
}

.tasks::-webkit-scrollbar-track {
  background: transparent;
}

.tasks::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
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
</style>