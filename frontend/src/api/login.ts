import { request } from '@/utils/request'
import { encrypt } from '@/utils/crypto'

export const AuthApi = {
  login: (credentials: { username: string; password: string }) => {
    const entryCredentials = {
      username: encrypt(credentials.username),
      password: encrypt(credentials.password),
    }
    return request.post<{
      data: any
      token: string
    }>('/login/access-token', entryCredentials, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
  },
  logout: (data: any) => request.post('/login/logout', data),
  info: () => request.get('/user/info'),
}
