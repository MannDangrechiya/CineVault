// CineVault OS — Create Pick Room Screen (Part 3.1)
// Minimal form to spin up a new group "pick room": a title and a
// comma-separated list of candidate title IDs. A proper search/watchlist
// candidate picker is out of scope for this pass — see
// apps/mobile/lib/presentation/providers/social_provider.dart for the
// createPickRoom contract this posts to.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../providers/social_provider.dart';
import '../widgets/glass/glass.dart';
import 'pick_room_screen.dart';

class CreatePickRoomScreen extends ConsumerStatefulWidget {
  const CreatePickRoomScreen({super.key});

  @override
  ConsumerState<CreatePickRoomScreen> createState() => _CreatePickRoomScreenState();
}

class _CreatePickRoomScreenState extends ConsumerState<CreatePickRoomScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _candidateIdsController = TextEditingController();

  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _titleController.dispose();
    _candidateIdsController.dispose();
    super.dispose();
  }

  List<String> _parseCandidateIds() {
    return _candidateIdsController.text
        .split(',')
        .map((id) => id.trim())
        .where((id) => id.isNotEmpty)
        .toList();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      final room = await ref.read(socialRepositoryProvider).createPickRoom(
            title: _titleController.text.trim(),
            candidateTitleIds: _parseCandidateIds(),
          );

      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => PickRoomScreen(slug: room.slug)),
      );
    } catch (e) {
      setState(() {
        _errorMessage = '$e';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: const GlassAppBar(title: Text('New Pick Room')),
      body: Column(
        children: [
          GlassAppBar.contentSpacer(context),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Room Title', style: textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _titleController,
                      decoration: const InputDecoration(
                        hintText: 'e.g. Friday Movie Night',
                      ),
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Enter a room title.';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 20),
                    Text('Candidate Title IDs', style: textTheme.titleMedium),
                    const SizedBox(height: 4),
                    Text(
                      'Comma-separated title IDs (a proper title picker is '
                      'coming later).',
                      style: textTheme.bodySmall,
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _candidateIdsController,
                      decoration: const InputDecoration(
                        hintText: 'title-id-1, title-id-2, title-id-3',
                      ),
                      minLines: 1,
                      maxLines: 3,
                      validator: (value) {
                        if (_parseCandidateIds().isEmpty) {
                          return 'Enter at least one candidate title ID.';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 24),
                    if (_errorMessage != null)
                      GlassCard(
                        margin: const EdgeInsets.only(bottom: 16),
                        tintColor: AppTheme.stateError,
                        child: Text(
                          _errorMessage!,
                          style: const TextStyle(color: AppTheme.stateError),
                        ),
                      ),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        icon: _isSubmitting
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.how_to_vote),
                        label: Text(_isSubmitting ? 'Creating Room...' : 'Create Pick Room'),
                        onPressed: _isSubmitting ? null : _submit,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
