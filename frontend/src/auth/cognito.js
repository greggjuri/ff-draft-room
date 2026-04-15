import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
} from 'amazon-cognito-identity-js'

const poolData = {
  UserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || '',
  ClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || '',
}

const userPool = poolData.UserPoolId ? new CognitoUserPool(poolData) : null

export function login(email, password) {
  return new Promise((resolve, reject) => {
    if (!userPool) {
      reject(new Error('Cognito not configured'))
      return
    }
    const user = new CognitoUser({ Username: email, Pool: userPool })
    const authDetails = new AuthenticationDetails({
      Username: email,
      Password: password,
    })
    user.authenticateUser(authDetails, {
      onSuccess: (session) => resolve(session),
      onFailure: (err) => reject(err),
    })
  })
}

export function logout() {
  if (!userPool) return
  const user = userPool.getCurrentUser()
  if (user) user.signOut()
}

export function getToken() {
  if (!userPool) return null
  const user = userPool.getCurrentUser()
  if (!user) return null

  return new Promise((resolve) => {
    user.getSession((err, session) => {
      if (err || !session?.isValid()) {
        resolve(null)
        return
      }
      resolve(session.getIdToken().getJwtToken())
    })
  })
}

export function getCurrentUser() {
  if (!userPool) return Promise.resolve(null)
  const user = userPool.getCurrentUser()
  if (!user) return Promise.resolve(null)

  return new Promise((resolve) => {
    user.getSession((err, session) => {
      if (err || !session?.isValid()) {
        resolve(null)
        return
      }
      resolve({
        email: user.getUsername(),
        token: session.getIdToken().getJwtToken(),
      })
    })
  })
}

export const isCognitoConfigured = () => !!userPool
