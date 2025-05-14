export const namespaced = true;

export const state = () => ({
  // history: { [taskId]: [ { user, action, ts }, … ] }
  history: {}
});

export const mutations = {
  INIT_HISTORY(state, { taskId, events }) {
    state.history = { ...state.history, [taskId]: events };
  },
  ADD_EVENT(state, { taskId, event }) {
    const h = state.history[taskId] || [];
    state.history = { 
      ...state.history, 
      [taskId]: [...h, event]
    };
  }
};

export const getters = {
  getHistory: (state) => (taskId) => {
    return state.history[taskId] || [];
  }
};
