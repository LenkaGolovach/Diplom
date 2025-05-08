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
        v-model="newName"
        @blur="stopEditing"
        @keyup.enter="stopEditing"
        class="column-title-input"
      />
      <button @click="deleteColumn" class="delete-column-button">×</button>
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
          @click="openTaskModal(element)"
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
  },
  data() {
    return {
      tasks: Array.isArray(this.column.tasks) ? [...this.column.tasks] : [],
      isEditing: false,
      showTaskForm: false,
      newTaskName: '',
      newName: this.column.name,
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
      this.updateColumn();
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
      console.log('Draggable change event:', event);
      const movedTask = event.moved ? event.moved.element : null;
      const addedTask = event.added ? event.added.element : null;
      const removedTask = event.removed ? event.removed.element : null;

      // Обновляем весь список задач для родителя, чтобы он обновил пропсы
      this.$emit('update-tasks', this.tasks); 

      // Отправляем изменения порядка на сервер
      this.tasks.forEach((task, index) => {
         if (task.order !== index || (addedTask && task.id === addedTask.id)) { 
           this.updateTaskOrder(task, index);
         }
      });
    },
    async updateTaskOrder(task, newOrder) {
        try {
            await axios.patch(`/api/tasks/${task.id}/`, {
                column: this.column.id,
                order: newOrder
            }, {
                headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
            });
            task.order = newOrder; // Обновляем локально для консистентности
        } catch (error) {
            console.error(`Ошибка обновления порядка для задачи ${task.id}:`, error);
            // Возможно, стоит откатить изменение в UI или показать ошибку
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
    async updateColumn() {
      try {
        const response = await axios.patch(
          `/api/columns/${this.column.id}/`,
          { name: this.newName },
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`,
            },
          }
        );
        this.column.name = this.newName;
        this.$emit('update-column', { ...this.column, name: this.newName });
        this.isEditing = false;
      } catch (error) {
        console.error('Ошибка обновления колонки:', error);
      }
    },
    openTaskModal(task) {
      this.$emit('openTaskModal', task);
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
    'column.tasks': {
      handler(newTasks) {
        this.tasks = Array.isArray(newTasks) ? [...newTasks] : [];
      },
      deep: true
    }
  }
};
</script>

<style scoped>
.column {
  background-color: #f8f9fa;
  border-radius: 12px;
  padding: 0;
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 180px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.color-stripe {
  height: 6px;
  border-radius: 12px 12px 0 0;
  margin-bottom: 10px;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
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
</style>