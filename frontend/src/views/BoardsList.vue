<template>
  <div class="boards-list">
    <div class="content-wrapper">
      <div class="header">
        <h1>Мои проекты</h1>
        <div class="header-buttons">
          <button class="add-board-button" @click="showCreateModal">
            <span class="icon">+</span>
            Создать доску
          </button>
          <button class="logout-button" @click="logout">
            <span class="icon">↪</span>
            Выйти
          </button>
        </div>
      </div>

      <div class="board-cards">
        <div
          v-for="board in boards"
          :key="board.id"
          class="board-card"
          @click="goToBoard(board.id)"
        >
          <div class="board-card-content">
            <h3>{{ board.name }}</h3>
            <button @click.stop="confirmDelete(board)" class="delete-board-btn">
              <span class="icon">×</span>
            </button>
          </div>
        </div>
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
  min-height: 100vh;
  width: 100%;
  padding: 40px 20px;
  background: linear-gradient(135deg, 
    #ffffff 0%,
    #fff5f5 25%,
    #f8f7ff 50%,
    #fff5f5 75%,
    #ffffff 100%
  );
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
}

body {
  margin: 0;
  padding: 0;
  min-height: 100vh;
  background: linear-gradient(135deg, 
    #ffffff 0%,
    #fff5f5 25%,
    #f8f7ff 50%,
    #fff5f5 75%,
    #ffffff 100%
  );
}

.content-wrapper {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
  padding: 20px 30px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 16px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.header h1 {
  font-size: 2.5em;
  color: #2c3e50;
  margin: 0;
  font-weight: 600;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.header-buttons {
  display: flex;
  gap: 15px;
}

.add-board-button, .logout-button {
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: 0.3px;
}

.add-board-button {
  background: #5b9cff;
  color: white;
  box-shadow: 0 4px 15px rgba(91, 156, 255, 0.3);
}

.add-board-button:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91, 156, 255, 0.4);
}

.logout-button {
  background: #ff7b93;
  color: white;
  box-shadow: 0 4px 15px rgba(255, 123, 147, 0.3);
}

.logout-button:hover {
  background: #ff6a85;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 123, 147, 0.4);
}

.board-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 25px;
  padding: 20px;
}

.board-card {
  height: 180px;
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 2px;
  background: #ffb5ba;
  transform: rotate(-2deg);
}

.board-card:nth-child(3n+1) {
  background: #b5c7ee;
  transform: rotate(1deg);
}

.board-card:nth-child(3n+2) {
  background: #ffd6a5;
  transform: rotate(-1deg);
}

.board-card:nth-child(3n+3) {
  background: #e1c1eb;
  transform: rotate(2deg);
}

.board-card::before {
  content: '';
  position: absolute;
  right: 0;
  bottom: 0;
  width: 25px;
  height: 25px;
  background: linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.06) 50%);
  border-radius: 0 0 2px 0;
}

.board-card::after {
  content: '';
  position: absolute;
  right: 0;
  bottom: 0;
  width: 15px;
  height: 15px;
  background: linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.03) 50%);
  border-radius: 0 0 2px 0;
}

.board-card:hover {
  transform: translateY(-5px) rotate(0deg) !important;
  box-shadow: 0 5px 15px rgba(0,0,0,0.08);
}

.board-card-content {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.board-card h3 {
  color: rgba(0,0,0,0.7);
  margin: 0;
  font-size: 1.2em;
  font-weight: 500;
  word-break: break-word;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.delete-board-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: transparent;
  border: none;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(0,0,0,0.4);
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  opacity: 0;
  z-index: 2;
}

.board-card:hover .delete-board-btn {
  opacity: 1;
}

.delete-board-btn:hover {
  color: rgba(0,0,0,0.7);
  transform: rotate(90deg);
}

.icon {
  font-size: 1.2em;
  line-height: 1;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
    padding: 20px;
    margin: 0 10px 30px 10px;
  }

  .header h1 {
    font-size: 2em;
  }

  .header-buttons {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
  }

  .add-board-button, .logout-button {
    width: 100%;
    justify-content: center;
  }

  .board-cards {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 15px;
    padding: 10px;
  }

  .board-card {
    height: 150px;
  }
}
</style>