<template>
  <div class="boards-list">
    <div class="header">
      <h1>Мои проекты</h1>
      <button class="add-board-button" @click="showCreateModal">+ Создать доску</button>
      <button class="logout-button" @click="logout">Выйти</button>
    </div>
    <div class="board-cards">
      <div
        v-for="board in boards"
        :key="board.id"
        class="board-card"
        @click="goToBoard(board.id)"
      >
        {{ board.name }}
        <button @click.stop="confirmDelete(board)" class="delete-board-btn">×</button>
      </div>
    </div>

    <ConfirmationModal
      v-if="showDeleteModal"
      title="Удаление доски"
      :message="deleteMessage"
      confirm-text="Удалить"
      @confirm="deleteBoard"
      @close="closeDeleteModal"
    />

    <CreateBoardModal
      v-if="showCreateBoardModal"
      @create="createBoard"
      @close="closeCreateModal"
    />

  </div>
</template>

<script>
import axios from 'axios';
import ConfirmationModal from '@/components/ConfirmationModel.vue' 
import CreateBoardModal from '@/components/CreateBoardModel.vue'

export default {
  computed: {
    deleteMessage() {
      return this.selectedBoard
        ? `Вы уверены, что хотите удалить доску «${this.selectedBoard.name}»?`
        : 'Вы уверены, что хотите удалить эту доску?';
    }
  },
  components: {
    ConfirmationModal,
    CreateBoardModal
  },
  data() {
    return {
      boards: [],
      showDeleteModal: false,
      showCreateBoardModal: false,
      selectedBoard: null
    };
  },
  async created() {
    await this.fetchBoards();
  },
  methods: {
    async fetchBoards() {
      try {
        const response = await axios.get('/api/boards/', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        this.boards = response.data.results || response.data; // Обработка пагинации
      } catch (error) {
        const errorMessage = error.response && error.response.data 
          ? error.response.data 
          : error.message;
        console.error('Ошибка загрузки досок:', errorMessage);
      }
    },
    confirmDelete(board) {
      this.selectedBoard = {...board};
      this.showDeleteModal = true;
    },
    async deleteBoard() {
      if (!this.selectedBoard) return; // Защита от null

      try {
        const boardId = this.selectedBoard.id; // Сохраняем ID заранее
        await axios.delete(`/api/boards/${boardId}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        // Фильтруем доски по сохраненному ID
        this.boards = this.boards.filter(b => b.id !== boardId);
        this.closeDeleteModal();
      } catch (error) {
        console.error('Ошибка удаления доски:', error);
      }
    },
    closeDeleteModal() {
      this.showDeleteModal = false
      this.selectedBoard = null
    },
    showCreateModal() {
      this.showCreateBoardModal = true
    },
    closeCreateModal() {
      this.showCreateBoardModal = false
    },
    async createBoard(name) {
      try {
        const response = await axios.post(
          '/api/boards/',
          { name },
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'application/json'
            },
          }
        );
        this.boards = [response.data, ...this.boards];
        this.closeCreateModal();
      } catch (error) {
        console.error('Ошибка создания доски:', error.response.data);
        alert('Не удалось создать доску. Проверьте введенные данные.');
      }
    },
    goToBoard(boardId) {
      this.$router.push(`/boards/${boardId}`);
    },
    logout() {
      localStorage.removeItem('token');
      this.$router.push('/login');
    },
  },
};
</script>

<style scoped>
.boards-list {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.add-board-button {
  background: #0079bf;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.add-board-button:hover {
  background: #026aa7;
}

.logout-button {
  background: #eb5a46;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.logout-button:hover {
  background: #cf513d;
}

.board-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.board-card {
  position: relative; 
  background: white;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 200px;
  cursor: pointer;
}

.board-card:hover {
  background: #f5f6f8;
}

.delete-board-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  background: none;
  border: none;
  color: #5e6c84;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
}

.delete-board-btn:hover {
  color: #ff4444;
}
</style>