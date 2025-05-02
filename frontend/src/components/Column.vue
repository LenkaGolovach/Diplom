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
        <div class="task-card">
          <div class="task-header" @click="openTaskModal(element)">
            <div class="task-title">{{ element.name }}</div>
            <div class="priority-label" :class="getPriorityClass(element.priority)">
              {{ getPriorityText(element.priority) }}
            </div>
          </div>
          <div class="task-meta">
            <div v-if="element.subtasks && element.subtasks.length > 0" class="subtasks-info">
              {{ getCompletedSubtasksCount(element) }}/{{ element.subtasks.length }}
            </div>
            <div v-if="element.attachments && element.attachments.length > 0" class="attachments-info">
              📎 {{ element.attachments.length }}
            </div>
          </div>
        </div>
      </template>
    </draggable>

    <button @click="addTask" class="add-task-button">
      + Добавить задачу
    </button>
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
      tasks: this.column.tasks,
      isEditing: false,
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
        // Обновляем локальное состояние сразу
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
    handleTaskSave(updatedTask) {
      const index = this.tasks.findIndex(t => t.id === updatedTask.id);
      if (index !== -1) {
        // Обновляем существующую задачу
        this.tasks.splice(index, 1, {
          ...updatedTask,
          subtasks: updatedTask.subtasks || [],
          files: updatedTask.attachments || []
        });
      } else {
        // Добавляем новую задачу
        this.tasks.push({
          ...updatedTask,
          subtasks: updatedTask.subtasks || [],
          files: updatedTask.attachments || []
        });
      }
    },
  },
  watch: {
    column: {
      handler(newColumn) {
        this.newName = newColumn.name;
      },
      deep: true
    }
  },
  setup(props, { emit }) {
    const isEditing = ref(false);
    const newName = ref(props.column.name);

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

    const getCompletedSubtasksCount = (task) => {
      return task.subtasks.filter((subtask) => subtask.completed).length;
    };

    const addTask = () => {
      emit('add-task');
    };

    const deleteColumn = () => {
      emit('delete-column');
    };

    const updateColumn = async () => {
      try {
        const response = await axios.patch(
          `/api/columns/${props.column.id}/`,
          { name: newName.value },
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`,
            },
          }
        );
        emit('update-column', { ...props.column, name: newName.value });
        isEditing.value = false;
      } catch (error) {
        console.error('Ошибка обновления колонки:', error);
      }
    };

    const openTaskModal = (task) => {
      emit('openTaskModal', task);
    };

    return {
      isEditing,
      newName,
      addTask,
      deleteColumn,
      updateColumn,
      getCompletedSubtasksCount,
      openTaskModal,
      getPriorityClass,
      getPriorityText
    };
  },
};
</script>

<style scoped>
.column {
  background: #f5f6f8;
  border-radius: 8px;
  width: 280px;
  margin: 0 12px;
  padding: 12px;
  position: relative;
}

.color-stripe {
  height: 4px;
  border-radius: 2px 2px 0 0;
  margin: -12px -12px 12px -12px;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.column-title {
  font-weight: 600;
  font-size: 15px;
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  flex: 1;
  color: #000000;
}

.column-title:hover {
  background: #ecedf0;
}

.column-title-input {
  font-weight: 600;
  font-size: 15px;
  width: 100%;
  padding: 8px;
  border: 2px solid #0079bf;
  border-radius: 4px;
  outline: none;
}

.delete-column-button {
  background: none;
  border: none;
  color: #5e6c84;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  margin-left: 8px;
  border-radius: 4px;
}

.delete-column-button:hover {
  background: #e0e0e0;
}

.tasks {
  min-height: 40px;
}

.add-task-button {
  width: 100%;
  padding: 8px;
  border: none;
  background: none;
  color: #5e6c84;
  cursor: pointer;
  border-radius: 4px;
  margin-top: 8px;
}

.add-task-button:hover {
  background: #ecedf0;
}

.task-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  cursor: pointer;
}

.task-card:hover {
  background: #f8f9fa;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.task-title {
  font-weight: 500;
  flex: 1;
  margin-right: 10px;
  color: #000000;
}

.priority-label {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: bold;
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
</style>