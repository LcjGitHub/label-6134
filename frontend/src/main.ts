import { createApp, h } from 'vue'
import naive, {
  NConfigProvider,
  NMessageProvider,
  NDialogProvider,
  zhCN,
  dateZhCN,
} from 'naive-ui'
import App from './App.vue'

const app = createApp({
  render: () =>
    h(
      NConfigProvider,
      { locale: zhCN, dateLocale: dateZhCN },
      {
        default: () =>
          h(NMessageProvider, null, {
            default: () =>
              h(NDialogProvider, null, {
                default: () => h(App),
              }),
          }),
      },
    ),
})

app.use(naive)
app.mount('#app')
