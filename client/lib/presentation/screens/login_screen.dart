// CineVault OS — Login / Authentication Screen (Phase 9.8)

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController(text: 'curator@cinevault.org');
  final _passwordController = TextEditingController(text: 'dev_password_123');

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submitLogin() {
    if (_formKey.currentState?.validate() ?? false) {
      ref.read(authProvider.notifier).login(
            _emailController.text.trim(),
            _passwordController.text.trim(),
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Icon(
                      Icons.movie_filter_rounded,
                      size: 64,
                      color: AppTheme.accentGold,
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'CineVault OS',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.2,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Sign in to access platform catalog & curation',
                      style: TextStyle(fontSize: 13, color: Colors.grey),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    if (authState.errorMessage != null) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.red.shade900.withValues(alpha: 0.4),
                          border: Border.all(color: Colors.redAccent),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          authState.errorMessage!,
                          style: const TextStyle(color: Colors.redAccent, fontSize: 13),
                          textAlign: TextAlign.center,
                        ),
                      ),
                      const SizedBox(height: 20),
                    ],
                    TextFormField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        labelText: 'Email Address',
                        prefixIcon: Icon(Icons.email_outlined),
                        border: OutlineInputBorder(),
                      ),
                      validator: (val) {
                        if (val == null || val.trim().isEmpty) {
                          return 'Please enter your email address.';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _passwordController,
                      obscureText: true,
                      decoration: const InputDecoration(
                        labelText: 'Password',
                        prefixIcon: Icon(Icons.lock_outline),
                        border: OutlineInputBorder(),
                      ),
                      validator: (val) {
                        if (val == null || val.trim().isEmpty) {
                          return 'Please enter your password.';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        backgroundColor: AppTheme.accentGold,
                        foregroundColor: Colors.black,
                      ),
                      onPressed: authState.isLoading ? null : _submitLogin,
                      child: authState.isLoading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                            )
                          : const Text(
                              'SIGN IN',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                            ),
                    ),
                    const SizedBox(height: 24),
                    Wrap(
                      alignment: WrapAlignment.spaceEvenly,
                      spacing: 8,
                      children: [
                        TextButton(
                          onPressed: () {
                            _emailController.text = 'user@cinevault.org';
                            _passwordController.text = 'password123';
                          },
                          child: const Text('Fill User Demo'),
                        ),
                        TextButton(
                          onPressed: () {
                            _emailController.text = 'curator@cinevault.org';
                            _passwordController.text = 'password123';
                          },
                          child: const Text('Fill Curator Demo'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
