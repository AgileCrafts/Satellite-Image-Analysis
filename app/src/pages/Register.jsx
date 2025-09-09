import React from 'react';
import { Button, Checkbox, Form, Input, Typography } from 'antd';

const { Title } = Typography;

const Register = () => {
  const onFinish = (values) => {
    console.log('Registration Success:', values);
    // You can later send this to backend API
  };

  const onFinishFailed = (errorInfo) => {
    console.log('Registration Failed:', errorInfo);
  };

  return (
    <div className="register">
      <Title level={2} style={{ textAlign: 'center', marginBottom: 20 }}>
        Registration
      </Title>

      <Form
        className="register-form"
        name="register"
        requiredMark={false}
        layout="vertical"
        style={{ maxWidth: 600 }}
        initialValues={{ agreement: false }}
        onFinish={onFinish}
        onFinishFailed={onFinishFailed}
        autoComplete="off"
      >
        {/* Username */}
        <Form.Item
          label="Username"
          name="username"
          rules={[{ required: true, message: 'Please input your username!' }]}
        >
          <Input />
        </Form.Item>

        {/* Email */}
        <Form.Item
          label="Email"
          name="email"
          rules={[
            { required: true, message: 'Please input your email!' },
            { type: 'email', message: 'Please enter a valid email!' },
          ]}
        >
          <Input />
        </Form.Item>

        {/* Password */}
        <Form.Item
          label="Password"
          name="password"
          rules={[{ required: true, message: 'Please input your password!' }]}
        >
          <Input.Password />
        </Form.Item>

        {/* Confirm Password */}
        <Form.Item
          label="Confirm Password"
          name="confirmPassword"
          dependencies={['password']}
          rules={[
            { required: true, message: 'Please confirm your password!' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('Passwords do not match!'));
              },
            }),
          ]}
        >
          <Input.Password />
        </Form.Item>

        {/* Agreement Checkbox */}
        <Form.Item
          name="agreement"
          valuePropName="checked"
          rules={[
            {
              validator: (_, value) =>
                value
                  ? Promise.resolve()
                  : Promise.reject(new Error('You must accept the agreement')),
            },
          ]}
        >
          <Checkbox>I agree to the <a>terms and conditions</a></Checkbox>
        </Form.Item>

        {/* Submit */}
        <Form.Item>
          <Button type="primary" htmlType="submit" block>
            Register
          </Button>
        </Form.Item>

        <Form.Item>
          <p>
            Have an account? <a href="/">Login</a>
          </p>
        </Form.Item>
      </Form>
    </div>
  );
};

export default Register;
