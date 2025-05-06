document.addEventListener('DOMContentLoaded', function() {
    // 切換表單
    const tabButtons = document.querySelectorAll('.tab-button');
    const formContainers = document.querySelectorAll('.form-container');
    const switchToRegister = document.getElementById('switch-to-register');
    const switchToLogin = document.getElementById('switch-to-login');

    function switchTab(tabId) {
        tabButtons.forEach(button => {
            button.classList.toggle('active', button.getAttribute('data-tab') === tabId);
        });

        formContainers.forEach(container => {
            container.classList.toggle('active', container.id === tabId + '-form');
        });
    }

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            switchTab(this.getAttribute('data-tab'));
        });
    });

    switchToRegister.addEventListener('click', function(e) {
        e.preventDefault();
        switchTab('register');
    });

    switchToLogin.addEventListener('click', function(e) {
        e.preventDefault();
        switchTab('login');
    });

//     // 表單提交處理
//     const loginForm = document.getElementById('loginForm');
//     const registerForm = document.getElementById('registerForm');
//
//     loginForm.addEventListener('submit', function(e) {
//         e.preventDefault();
//
//         // 清除錯誤訊息
//         clearErrors();
//
//         // 獲取表單數據
//         const email = document.getElementById('login-email').value;
//         const password = document.getElementById('login-password').value;
//
//         // 這裡可以添加表單驗證
//         let isValid = true;
//
//         if (!email) {
//             showError('login-email-error', '請輸入電子郵件');
//             isValid = false;
//         }
//
//         if (!password) {
//             showError('login-password-error', '請輸入密碼');
//             isValid = false;
//         }
//
//         if (isValid) {
//             // 模擬 AJAX 請求
//             simulateAjaxRequest({
//                 form_type: 'login',
//                 email: email,
//                 password: password
//             }, function(response) {
//                 if (response.success) {
//                     showSuccess('login-success', '登入成功！正在跳轉...');
//                     // 模擬跳轉
//                     setTimeout(() => {
//                         window.location.href = '/dashboard';
//                     }, 1500);
//                 } else {
//                     if (response.errors) {
//                         for (const field in response.errors) {
//                             showError(`login-${field}-error`, response.errors[field]);
//                         }
//                     }
//                 }
//             });
//         }
//     });
//
//     registerForm.addEventListener('submit', function(e) {
//         e.preventDefault();
//
//         // 清除錯誤訊息
//         clearErrors();
//
//         // 獲取表單數據
//         const role = document.getElementById('register-role').value;
//         const email = document.getElementById('register-email').value;
//         const username = document.getElementById('register-username').value;
//         const password = document.getElementById('register-password').value;
//         const confirmPassword = document.getElementById('register-confirm-password').value;
//
//         // 表單驗證
//         let isValid = true;
//
//         if (!role) {
//             showError('register-role-error', '請選擇身份');
//             isValid = false;
//         }
//
//         if (!email) {
//             showError('register-email-error', '請輸入電子郵件');
//             isValid = false;
//         }
//
//         if (!username) {
//             showError('register-username-error', '請輸入帳號名稱');
//             isValid = false;
//         }
//
//         if (!password) {
//             showError('register-password-error', '請輸入密碼');
//             isValid = false;
//         }
//
//         if (password !== confirmPassword) {
//             showError('register-confirm-password-error', '兩次輸入的密碼不一致');
//             isValid = false;
//         }
//
//         if (isValid) {
//             // 模擬 AJAX 請求
//             simulateAjaxRequest({
//                 form_type: 'register',
//                 role: role,
//                 email: email,
//                 username: username,
//                 password: password
//             }, function(response) {
//                 if (response.success) {
//                     showSuccess('register-success', '註冊成功！正在跳轉...');
//                     // 模擬跳轉
//                     setTimeout(() => {
//                         window.location.href = '/dashboard';
//                     }, 1500);
//                 } else {
//                     if (response.errors) {
//                         for (const field in response.errors) {
//                             showError(`register-${field}-error`, response.errors[field]);
//                         }
//                     }
//                 }
//             });
//         }
//     });
//
//     function clearErrors() {
//         document.querySelectorAll('.error-message').forEach(el => {
//             el.style.display = 'none';
//             el.textContent = '';
//         });
//
//         document.querySelectorAll('.success-message').forEach(el => {
//             el.style.display = 'none';
//             el.textContent = '';
//         });
//     }
//
//     function showError(id, message) {
//         const errorElement = document.getElementById(id);
//         errorElement.textContent = message;
//         errorElement.style.display = 'block';
//     }
//
//     function showSuccess(id, message) {
//         const successElement = document.getElementById(id);
//         successElement.textContent = message;
//         successElement.style.display = 'block';
//     }
//
//     // 模擬 AJAX 請求
//     function simulateAjaxRequest(data, callback) {
//         // 這裡只是模擬，實際應用中應該使用 fetch 或 XMLHttpRequest
//         setTimeout(() => {
//             if (data.form_type === 'login') {
//                 // 模擬登入驗證
//                 if (data.email === 'test@example.com' && data.password === 'password') {
//                     callback({
//                         success: true,
//                         message: '登入成功'
//                     });
//                 } else {
//                     callback({
//                         success: false,
//                         errors: {
//                             'email': '電子郵件或密碼不正確',
//                             'password': '電子郵件或密碼不正確'
//                         }
//                     });
//                 }
//             } else if (data.form_type === 'register') {
//                 // 模擬註冊驗證
//                 if (data.email === 'test@example.com') {
//                     callback({
//                         success: false,
//                         errors: {
//                             'email': '此電子郵件已被註冊'
//                         }
//                     });
//                 } else {
//                     callback({
//                         success: true,
//                         message: '註冊成功'
//                     });
//                 }
//             }
//         }, 1000);
//     }
});