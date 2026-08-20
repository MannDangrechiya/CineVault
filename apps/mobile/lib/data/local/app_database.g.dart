// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $OutboxMutationsTable extends OutboxMutations
    with TableInfo<$OutboxMutationsTable, OutboxMutationRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $OutboxMutationsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _mutationIdMeta = const VerificationMeta(
    'mutationId',
  );
  @override
  late final GeneratedColumn<String> mutationId = GeneratedColumn<String>(
    'mutation_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _mutationTypeMeta = const VerificationMeta(
    'mutationType',
  );
  @override
  late final GeneratedColumn<String> mutationType = GeneratedColumn<String>(
    'mutation_type',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _clientTimestampMeta = const VerificationMeta(
    'clientTimestamp',
  );
  @override
  late final GeneratedColumn<String> clientTimestamp = GeneratedColumn<String>(
    'client_timestamp',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _payloadJsonMeta = const VerificationMeta(
    'payloadJson',
  );
  @override
  late final GeneratedColumn<String> payloadJson = GeneratedColumn<String>(
    'payload_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('PENDING'),
  );
  static const VerificationMeta _retryCountMeta = const VerificationMeta(
    'retryCount',
  );
  @override
  late final GeneratedColumn<int> retryCount = GeneratedColumn<int>(
    'retry_count',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  @override
  List<GeneratedColumn> get $columns => [
    mutationId,
    mutationType,
    clientTimestamp,
    payloadJson,
    status,
    retryCount,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'outbox_mutations';
  @override
  VerificationContext validateIntegrity(
    Insertable<OutboxMutationRow> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('mutation_id')) {
      context.handle(
        _mutationIdMeta,
        mutationId.isAcceptableOrUnknown(data['mutation_id']!, _mutationIdMeta),
      );
    } else if (isInserting) {
      context.missing(_mutationIdMeta);
    }
    if (data.containsKey('mutation_type')) {
      context.handle(
        _mutationTypeMeta,
        mutationType.isAcceptableOrUnknown(
          data['mutation_type']!,
          _mutationTypeMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_mutationTypeMeta);
    }
    if (data.containsKey('client_timestamp')) {
      context.handle(
        _clientTimestampMeta,
        clientTimestamp.isAcceptableOrUnknown(
          data['client_timestamp']!,
          _clientTimestampMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_clientTimestampMeta);
    }
    if (data.containsKey('payload_json')) {
      context.handle(
        _payloadJsonMeta,
        payloadJson.isAcceptableOrUnknown(
          data['payload_json']!,
          _payloadJsonMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_payloadJsonMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    }
    if (data.containsKey('retry_count')) {
      context.handle(
        _retryCountMeta,
        retryCount.isAcceptableOrUnknown(data['retry_count']!, _retryCountMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {mutationId};
  @override
  OutboxMutationRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return OutboxMutationRow(
      mutationId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}mutation_id'],
      )!,
      mutationType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}mutation_type'],
      )!,
      clientTimestamp: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}client_timestamp'],
      )!,
      payloadJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}payload_json'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      retryCount: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}retry_count'],
      )!,
    );
  }

  @override
  $OutboxMutationsTable createAlias(String alias) {
    return $OutboxMutationsTable(attachedDatabase, alias);
  }
}

class OutboxMutationRow extends DataClass
    implements Insertable<OutboxMutationRow> {
  final String mutationId;
  final String mutationType;
  final String clientTimestamp;
  final String payloadJson;
  final String status;
  final int retryCount;
  const OutboxMutationRow({
    required this.mutationId,
    required this.mutationType,
    required this.clientTimestamp,
    required this.payloadJson,
    required this.status,
    required this.retryCount,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['mutation_id'] = Variable<String>(mutationId);
    map['mutation_type'] = Variable<String>(mutationType);
    map['client_timestamp'] = Variable<String>(clientTimestamp);
    map['payload_json'] = Variable<String>(payloadJson);
    map['status'] = Variable<String>(status);
    map['retry_count'] = Variable<int>(retryCount);
    return map;
  }

  OutboxMutationsCompanion toCompanion(bool nullToAbsent) {
    return OutboxMutationsCompanion(
      mutationId: Value(mutationId),
      mutationType: Value(mutationType),
      clientTimestamp: Value(clientTimestamp),
      payloadJson: Value(payloadJson),
      status: Value(status),
      retryCount: Value(retryCount),
    );
  }

  factory OutboxMutationRow.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return OutboxMutationRow(
      mutationId: serializer.fromJson<String>(json['mutationId']),
      mutationType: serializer.fromJson<String>(json['mutationType']),
      clientTimestamp: serializer.fromJson<String>(json['clientTimestamp']),
      payloadJson: serializer.fromJson<String>(json['payloadJson']),
      status: serializer.fromJson<String>(json['status']),
      retryCount: serializer.fromJson<int>(json['retryCount']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'mutationId': serializer.toJson<String>(mutationId),
      'mutationType': serializer.toJson<String>(mutationType),
      'clientTimestamp': serializer.toJson<String>(clientTimestamp),
      'payloadJson': serializer.toJson<String>(payloadJson),
      'status': serializer.toJson<String>(status),
      'retryCount': serializer.toJson<int>(retryCount),
    };
  }

  OutboxMutationRow copyWith({
    String? mutationId,
    String? mutationType,
    String? clientTimestamp,
    String? payloadJson,
    String? status,
    int? retryCount,
  }) => OutboxMutationRow(
    mutationId: mutationId ?? this.mutationId,
    mutationType: mutationType ?? this.mutationType,
    clientTimestamp: clientTimestamp ?? this.clientTimestamp,
    payloadJson: payloadJson ?? this.payloadJson,
    status: status ?? this.status,
    retryCount: retryCount ?? this.retryCount,
  );
  OutboxMutationRow copyWithCompanion(OutboxMutationsCompanion data) {
    return OutboxMutationRow(
      mutationId: data.mutationId.present
          ? data.mutationId.value
          : this.mutationId,
      mutationType: data.mutationType.present
          ? data.mutationType.value
          : this.mutationType,
      clientTimestamp: data.clientTimestamp.present
          ? data.clientTimestamp.value
          : this.clientTimestamp,
      payloadJson: data.payloadJson.present
          ? data.payloadJson.value
          : this.payloadJson,
      status: data.status.present ? data.status.value : this.status,
      retryCount: data.retryCount.present
          ? data.retryCount.value
          : this.retryCount,
    );
  }

  @override
  String toString() {
    return (StringBuffer('OutboxMutationRow(')
          ..write('mutationId: $mutationId, ')
          ..write('mutationType: $mutationType, ')
          ..write('clientTimestamp: $clientTimestamp, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('status: $status, ')
          ..write('retryCount: $retryCount')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    mutationId,
    mutationType,
    clientTimestamp,
    payloadJson,
    status,
    retryCount,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is OutboxMutationRow &&
          other.mutationId == this.mutationId &&
          other.mutationType == this.mutationType &&
          other.clientTimestamp == this.clientTimestamp &&
          other.payloadJson == this.payloadJson &&
          other.status == this.status &&
          other.retryCount == this.retryCount);
}

class OutboxMutationsCompanion extends UpdateCompanion<OutboxMutationRow> {
  final Value<String> mutationId;
  final Value<String> mutationType;
  final Value<String> clientTimestamp;
  final Value<String> payloadJson;
  final Value<String> status;
  final Value<int> retryCount;
  final Value<int> rowid;
  const OutboxMutationsCompanion({
    this.mutationId = const Value.absent(),
    this.mutationType = const Value.absent(),
    this.clientTimestamp = const Value.absent(),
    this.payloadJson = const Value.absent(),
    this.status = const Value.absent(),
    this.retryCount = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  OutboxMutationsCompanion.insert({
    required String mutationId,
    required String mutationType,
    required String clientTimestamp,
    required String payloadJson,
    this.status = const Value.absent(),
    this.retryCount = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : mutationId = Value(mutationId),
       mutationType = Value(mutationType),
       clientTimestamp = Value(clientTimestamp),
       payloadJson = Value(payloadJson);
  static Insertable<OutboxMutationRow> custom({
    Expression<String>? mutationId,
    Expression<String>? mutationType,
    Expression<String>? clientTimestamp,
    Expression<String>? payloadJson,
    Expression<String>? status,
    Expression<int>? retryCount,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (mutationId != null) 'mutation_id': mutationId,
      if (mutationType != null) 'mutation_type': mutationType,
      if (clientTimestamp != null) 'client_timestamp': clientTimestamp,
      if (payloadJson != null) 'payload_json': payloadJson,
      if (status != null) 'status': status,
      if (retryCount != null) 'retry_count': retryCount,
      if (rowid != null) 'rowid': rowid,
    });
  }

  OutboxMutationsCompanion copyWith({
    Value<String>? mutationId,
    Value<String>? mutationType,
    Value<String>? clientTimestamp,
    Value<String>? payloadJson,
    Value<String>? status,
    Value<int>? retryCount,
    Value<int>? rowid,
  }) {
    return OutboxMutationsCompanion(
      mutationId: mutationId ?? this.mutationId,
      mutationType: mutationType ?? this.mutationType,
      clientTimestamp: clientTimestamp ?? this.clientTimestamp,
      payloadJson: payloadJson ?? this.payloadJson,
      status: status ?? this.status,
      retryCount: retryCount ?? this.retryCount,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (mutationId.present) {
      map['mutation_id'] = Variable<String>(mutationId.value);
    }
    if (mutationType.present) {
      map['mutation_type'] = Variable<String>(mutationType.value);
    }
    if (clientTimestamp.present) {
      map['client_timestamp'] = Variable<String>(clientTimestamp.value);
    }
    if (payloadJson.present) {
      map['payload_json'] = Variable<String>(payloadJson.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (retryCount.present) {
      map['retry_count'] = Variable<int>(retryCount.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('OutboxMutationsCompanion(')
          ..write('mutationId: $mutationId, ')
          ..write('mutationType: $mutationType, ')
          ..write('clientTimestamp: $clientTimestamp, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('status: $status, ')
          ..write('retryCount: $retryCount, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedTitlesTable extends CachedTitles
    with TableInfo<$CachedTitlesTable, CachedTitleRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedTitlesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _titleIdMeta = const VerificationMeta(
    'titleId',
  );
  @override
  late final GeneratedColumn<String> titleId = GeneratedColumn<String>(
    'title_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _displayIdMeta = const VerificationMeta(
    'displayId',
  );
  @override
  late final GeneratedColumn<String> displayId = GeneratedColumn<String>(
    'display_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _primaryTitleMeta = const VerificationMeta(
    'primaryTitle',
  );
  @override
  late final GeneratedColumn<String> primaryTitle = GeneratedColumn<String>(
    'primary_title',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _contentTypeMeta = const VerificationMeta(
    'contentType',
  );
  @override
  late final GeneratedColumn<String> contentType = GeneratedColumn<String>(
    'content_type',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _releaseYearMeta = const VerificationMeta(
    'releaseYear',
  );
  @override
  late final GeneratedColumn<int> releaseYear = GeneratedColumn<int>(
    'release_year',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _posterUrlMeta = const VerificationMeta(
    'posterUrl',
  );
  @override
  late final GeneratedColumn<String> posterUrl = GeneratedColumn<String>(
    'poster_url',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _genresJsonMeta = const VerificationMeta(
    'genresJson',
  );
  @override
  late final GeneratedColumn<String> genresJson = GeneratedColumn<String>(
    'genres_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _cachedAtMeta = const VerificationMeta(
    'cachedAt',
  );
  @override
  late final GeneratedColumn<String> cachedAt = GeneratedColumn<String>(
    'cached_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _isAuthoritativeMeta = const VerificationMeta(
    'isAuthoritative',
  );
  @override
  late final GeneratedColumn<bool> isAuthoritative = GeneratedColumn<bool>(
    'is_authoritative',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_authoritative" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  @override
  List<GeneratedColumn> get $columns => [
    titleId,
    displayId,
    primaryTitle,
    contentType,
    releaseYear,
    posterUrl,
    genresJson,
    cachedAt,
    isAuthoritative,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_titles';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedTitleRow> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('title_id')) {
      context.handle(
        _titleIdMeta,
        titleId.isAcceptableOrUnknown(data['title_id']!, _titleIdMeta),
      );
    } else if (isInserting) {
      context.missing(_titleIdMeta);
    }
    if (data.containsKey('display_id')) {
      context.handle(
        _displayIdMeta,
        displayId.isAcceptableOrUnknown(data['display_id']!, _displayIdMeta),
      );
    } else if (isInserting) {
      context.missing(_displayIdMeta);
    }
    if (data.containsKey('primary_title')) {
      context.handle(
        _primaryTitleMeta,
        primaryTitle.isAcceptableOrUnknown(
          data['primary_title']!,
          _primaryTitleMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_primaryTitleMeta);
    }
    if (data.containsKey('content_type')) {
      context.handle(
        _contentTypeMeta,
        contentType.isAcceptableOrUnknown(
          data['content_type']!,
          _contentTypeMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_contentTypeMeta);
    }
    if (data.containsKey('release_year')) {
      context.handle(
        _releaseYearMeta,
        releaseYear.isAcceptableOrUnknown(
          data['release_year']!,
          _releaseYearMeta,
        ),
      );
    }
    if (data.containsKey('poster_url')) {
      context.handle(
        _posterUrlMeta,
        posterUrl.isAcceptableOrUnknown(data['poster_url']!, _posterUrlMeta),
      );
    }
    if (data.containsKey('genres_json')) {
      context.handle(
        _genresJsonMeta,
        genresJson.isAcceptableOrUnknown(data['genres_json']!, _genresJsonMeta),
      );
    } else if (isInserting) {
      context.missing(_genresJsonMeta);
    }
    if (data.containsKey('cached_at')) {
      context.handle(
        _cachedAtMeta,
        cachedAt.isAcceptableOrUnknown(data['cached_at']!, _cachedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_cachedAtMeta);
    }
    if (data.containsKey('is_authoritative')) {
      context.handle(
        _isAuthoritativeMeta,
        isAuthoritative.isAcceptableOrUnknown(
          data['is_authoritative']!,
          _isAuthoritativeMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {titleId};
  @override
  CachedTitleRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedTitleRow(
      titleId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}title_id'],
      )!,
      displayId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}display_id'],
      )!,
      primaryTitle: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}primary_title'],
      )!,
      contentType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}content_type'],
      )!,
      releaseYear: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}release_year'],
      ),
      posterUrl: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}poster_url'],
      ),
      genresJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}genres_json'],
      )!,
      cachedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}cached_at'],
      )!,
      isAuthoritative: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_authoritative'],
      )!,
    );
  }

  @override
  $CachedTitlesTable createAlias(String alias) {
    return $CachedTitlesTable(attachedDatabase, alias);
  }
}

class CachedTitleRow extends DataClass implements Insertable<CachedTitleRow> {
  final String titleId;
  final String displayId;
  final String primaryTitle;
  final String contentType;
  final int? releaseYear;
  final String? posterUrl;
  final String genresJson;
  final String cachedAt;
  final bool isAuthoritative;
  const CachedTitleRow({
    required this.titleId,
    required this.displayId,
    required this.primaryTitle,
    required this.contentType,
    this.releaseYear,
    this.posterUrl,
    required this.genresJson,
    required this.cachedAt,
    required this.isAuthoritative,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['title_id'] = Variable<String>(titleId);
    map['display_id'] = Variable<String>(displayId);
    map['primary_title'] = Variable<String>(primaryTitle);
    map['content_type'] = Variable<String>(contentType);
    if (!nullToAbsent || releaseYear != null) {
      map['release_year'] = Variable<int>(releaseYear);
    }
    if (!nullToAbsent || posterUrl != null) {
      map['poster_url'] = Variable<String>(posterUrl);
    }
    map['genres_json'] = Variable<String>(genresJson);
    map['cached_at'] = Variable<String>(cachedAt);
    map['is_authoritative'] = Variable<bool>(isAuthoritative);
    return map;
  }

  CachedTitlesCompanion toCompanion(bool nullToAbsent) {
    return CachedTitlesCompanion(
      titleId: Value(titleId),
      displayId: Value(displayId),
      primaryTitle: Value(primaryTitle),
      contentType: Value(contentType),
      releaseYear: releaseYear == null && nullToAbsent
          ? const Value.absent()
          : Value(releaseYear),
      posterUrl: posterUrl == null && nullToAbsent
          ? const Value.absent()
          : Value(posterUrl),
      genresJson: Value(genresJson),
      cachedAt: Value(cachedAt),
      isAuthoritative: Value(isAuthoritative),
    );
  }

  factory CachedTitleRow.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedTitleRow(
      titleId: serializer.fromJson<String>(json['titleId']),
      displayId: serializer.fromJson<String>(json['displayId']),
      primaryTitle: serializer.fromJson<String>(json['primaryTitle']),
      contentType: serializer.fromJson<String>(json['contentType']),
      releaseYear: serializer.fromJson<int?>(json['releaseYear']),
      posterUrl: serializer.fromJson<String?>(json['posterUrl']),
      genresJson: serializer.fromJson<String>(json['genresJson']),
      cachedAt: serializer.fromJson<String>(json['cachedAt']),
      isAuthoritative: serializer.fromJson<bool>(json['isAuthoritative']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'titleId': serializer.toJson<String>(titleId),
      'displayId': serializer.toJson<String>(displayId),
      'primaryTitle': serializer.toJson<String>(primaryTitle),
      'contentType': serializer.toJson<String>(contentType),
      'releaseYear': serializer.toJson<int?>(releaseYear),
      'posterUrl': serializer.toJson<String?>(posterUrl),
      'genresJson': serializer.toJson<String>(genresJson),
      'cachedAt': serializer.toJson<String>(cachedAt),
      'isAuthoritative': serializer.toJson<bool>(isAuthoritative),
    };
  }

  CachedTitleRow copyWith({
    String? titleId,
    String? displayId,
    String? primaryTitle,
    String? contentType,
    Value<int?> releaseYear = const Value.absent(),
    Value<String?> posterUrl = const Value.absent(),
    String? genresJson,
    String? cachedAt,
    bool? isAuthoritative,
  }) => CachedTitleRow(
    titleId: titleId ?? this.titleId,
    displayId: displayId ?? this.displayId,
    primaryTitle: primaryTitle ?? this.primaryTitle,
    contentType: contentType ?? this.contentType,
    releaseYear: releaseYear.present ? releaseYear.value : this.releaseYear,
    posterUrl: posterUrl.present ? posterUrl.value : this.posterUrl,
    genresJson: genresJson ?? this.genresJson,
    cachedAt: cachedAt ?? this.cachedAt,
    isAuthoritative: isAuthoritative ?? this.isAuthoritative,
  );
  CachedTitleRow copyWithCompanion(CachedTitlesCompanion data) {
    return CachedTitleRow(
      titleId: data.titleId.present ? data.titleId.value : this.titleId,
      displayId: data.displayId.present ? data.displayId.value : this.displayId,
      primaryTitle: data.primaryTitle.present
          ? data.primaryTitle.value
          : this.primaryTitle,
      contentType: data.contentType.present
          ? data.contentType.value
          : this.contentType,
      releaseYear: data.releaseYear.present
          ? data.releaseYear.value
          : this.releaseYear,
      posterUrl: data.posterUrl.present ? data.posterUrl.value : this.posterUrl,
      genresJson: data.genresJson.present
          ? data.genresJson.value
          : this.genresJson,
      cachedAt: data.cachedAt.present ? data.cachedAt.value : this.cachedAt,
      isAuthoritative: data.isAuthoritative.present
          ? data.isAuthoritative.value
          : this.isAuthoritative,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedTitleRow(')
          ..write('titleId: $titleId, ')
          ..write('displayId: $displayId, ')
          ..write('primaryTitle: $primaryTitle, ')
          ..write('contentType: $contentType, ')
          ..write('releaseYear: $releaseYear, ')
          ..write('posterUrl: $posterUrl, ')
          ..write('genresJson: $genresJson, ')
          ..write('cachedAt: $cachedAt, ')
          ..write('isAuthoritative: $isAuthoritative')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    titleId,
    displayId,
    primaryTitle,
    contentType,
    releaseYear,
    posterUrl,
    genresJson,
    cachedAt,
    isAuthoritative,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedTitleRow &&
          other.titleId == this.titleId &&
          other.displayId == this.displayId &&
          other.primaryTitle == this.primaryTitle &&
          other.contentType == this.contentType &&
          other.releaseYear == this.releaseYear &&
          other.posterUrl == this.posterUrl &&
          other.genresJson == this.genresJson &&
          other.cachedAt == this.cachedAt &&
          other.isAuthoritative == this.isAuthoritative);
}

class CachedTitlesCompanion extends UpdateCompanion<CachedTitleRow> {
  final Value<String> titleId;
  final Value<String> displayId;
  final Value<String> primaryTitle;
  final Value<String> contentType;
  final Value<int?> releaseYear;
  final Value<String?> posterUrl;
  final Value<String> genresJson;
  final Value<String> cachedAt;
  final Value<bool> isAuthoritative;
  final Value<int> rowid;
  const CachedTitlesCompanion({
    this.titleId = const Value.absent(),
    this.displayId = const Value.absent(),
    this.primaryTitle = const Value.absent(),
    this.contentType = const Value.absent(),
    this.releaseYear = const Value.absent(),
    this.posterUrl = const Value.absent(),
    this.genresJson = const Value.absent(),
    this.cachedAt = const Value.absent(),
    this.isAuthoritative = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedTitlesCompanion.insert({
    required String titleId,
    required String displayId,
    required String primaryTitle,
    required String contentType,
    this.releaseYear = const Value.absent(),
    this.posterUrl = const Value.absent(),
    required String genresJson,
    required String cachedAt,
    this.isAuthoritative = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : titleId = Value(titleId),
       displayId = Value(displayId),
       primaryTitle = Value(primaryTitle),
       contentType = Value(contentType),
       genresJson = Value(genresJson),
       cachedAt = Value(cachedAt);
  static Insertable<CachedTitleRow> custom({
    Expression<String>? titleId,
    Expression<String>? displayId,
    Expression<String>? primaryTitle,
    Expression<String>? contentType,
    Expression<int>? releaseYear,
    Expression<String>? posterUrl,
    Expression<String>? genresJson,
    Expression<String>? cachedAt,
    Expression<bool>? isAuthoritative,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (titleId != null) 'title_id': titleId,
      if (displayId != null) 'display_id': displayId,
      if (primaryTitle != null) 'primary_title': primaryTitle,
      if (contentType != null) 'content_type': contentType,
      if (releaseYear != null) 'release_year': releaseYear,
      if (posterUrl != null) 'poster_url': posterUrl,
      if (genresJson != null) 'genres_json': genresJson,
      if (cachedAt != null) 'cached_at': cachedAt,
      if (isAuthoritative != null) 'is_authoritative': isAuthoritative,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedTitlesCompanion copyWith({
    Value<String>? titleId,
    Value<String>? displayId,
    Value<String>? primaryTitle,
    Value<String>? contentType,
    Value<int?>? releaseYear,
    Value<String?>? posterUrl,
    Value<String>? genresJson,
    Value<String>? cachedAt,
    Value<bool>? isAuthoritative,
    Value<int>? rowid,
  }) {
    return CachedTitlesCompanion(
      titleId: titleId ?? this.titleId,
      displayId: displayId ?? this.displayId,
      primaryTitle: primaryTitle ?? this.primaryTitle,
      contentType: contentType ?? this.contentType,
      releaseYear: releaseYear ?? this.releaseYear,
      posterUrl: posterUrl ?? this.posterUrl,
      genresJson: genresJson ?? this.genresJson,
      cachedAt: cachedAt ?? this.cachedAt,
      isAuthoritative: isAuthoritative ?? this.isAuthoritative,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (titleId.present) {
      map['title_id'] = Variable<String>(titleId.value);
    }
    if (displayId.present) {
      map['display_id'] = Variable<String>(displayId.value);
    }
    if (primaryTitle.present) {
      map['primary_title'] = Variable<String>(primaryTitle.value);
    }
    if (contentType.present) {
      map['content_type'] = Variable<String>(contentType.value);
    }
    if (releaseYear.present) {
      map['release_year'] = Variable<int>(releaseYear.value);
    }
    if (posterUrl.present) {
      map['poster_url'] = Variable<String>(posterUrl.value);
    }
    if (genresJson.present) {
      map['genres_json'] = Variable<String>(genresJson.value);
    }
    if (cachedAt.present) {
      map['cached_at'] = Variable<String>(cachedAt.value);
    }
    if (isAuthoritative.present) {
      map['is_authoritative'] = Variable<bool>(isAuthoritative.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedTitlesCompanion(')
          ..write('titleId: $titleId, ')
          ..write('displayId: $displayId, ')
          ..write('primaryTitle: $primaryTitle, ')
          ..write('contentType: $contentType, ')
          ..write('releaseYear: $releaseYear, ')
          ..write('posterUrl: $posterUrl, ')
          ..write('genresJson: $genresJson, ')
          ..write('cachedAt: $cachedAt, ')
          ..write('isAuthoritative: $isAuthoritative, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $OfflineWatchEventsTable extends OfflineWatchEvents
    with TableInfo<$OfflineWatchEventsTable, OfflineWatchEventRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $OfflineWatchEventsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _watchEventIdMeta = const VerificationMeta(
    'watchEventId',
  );
  @override
  late final GeneratedColumn<String> watchEventId = GeneratedColumn<String>(
    'watch_event_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _titleIdMeta = const VerificationMeta(
    'titleId',
  );
  @override
  late final GeneratedColumn<String> titleId = GeneratedColumn<String>(
    'title_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _watchedAtMeta = const VerificationMeta(
    'watchedAt',
  );
  @override
  late final GeneratedColumn<String> watchedAt = GeneratedColumn<String>(
    'watched_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _progressPercentageMeta =
      const VerificationMeta('progressPercentage');
  @override
  late final GeneratedColumn<double> progressPercentage =
      GeneratedColumn<double>(
        'progress_percentage',
        aliasedName,
        false,
        type: DriftSqlType.double,
        requiredDuringInsert: false,
        defaultValue: const Constant(100.0),
      );
  static const VerificationMeta _notesMeta = const VerificationMeta('notes');
  @override
  late final GeneratedColumn<String> notes = GeneratedColumn<String>(
    'notes',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _isTombstonedMeta = const VerificationMeta(
    'isTombstoned',
  );
  @override
  late final GeneratedColumn<bool> isTombstoned = GeneratedColumn<bool>(
    'is_tombstoned',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_tombstoned" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  @override
  List<GeneratedColumn> get $columns => [
    watchEventId,
    titleId,
    watchedAt,
    progressPercentage,
    notes,
    isTombstoned,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'offline_watch_events';
  @override
  VerificationContext validateIntegrity(
    Insertable<OfflineWatchEventRow> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('watch_event_id')) {
      context.handle(
        _watchEventIdMeta,
        watchEventId.isAcceptableOrUnknown(
          data['watch_event_id']!,
          _watchEventIdMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_watchEventIdMeta);
    }
    if (data.containsKey('title_id')) {
      context.handle(
        _titleIdMeta,
        titleId.isAcceptableOrUnknown(data['title_id']!, _titleIdMeta),
      );
    } else if (isInserting) {
      context.missing(_titleIdMeta);
    }
    if (data.containsKey('watched_at')) {
      context.handle(
        _watchedAtMeta,
        watchedAt.isAcceptableOrUnknown(data['watched_at']!, _watchedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_watchedAtMeta);
    }
    if (data.containsKey('progress_percentage')) {
      context.handle(
        _progressPercentageMeta,
        progressPercentage.isAcceptableOrUnknown(
          data['progress_percentage']!,
          _progressPercentageMeta,
        ),
      );
    }
    if (data.containsKey('notes')) {
      context.handle(
        _notesMeta,
        notes.isAcceptableOrUnknown(data['notes']!, _notesMeta),
      );
    }
    if (data.containsKey('is_tombstoned')) {
      context.handle(
        _isTombstonedMeta,
        isTombstoned.isAcceptableOrUnknown(
          data['is_tombstoned']!,
          _isTombstonedMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {watchEventId};
  @override
  OfflineWatchEventRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return OfflineWatchEventRow(
      watchEventId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}watch_event_id'],
      )!,
      titleId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}title_id'],
      )!,
      watchedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}watched_at'],
      )!,
      progressPercentage: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}progress_percentage'],
      )!,
      notes: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}notes'],
      ),
      isTombstoned: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_tombstoned'],
      )!,
    );
  }

  @override
  $OfflineWatchEventsTable createAlias(String alias) {
    return $OfflineWatchEventsTable(attachedDatabase, alias);
  }
}

class OfflineWatchEventRow extends DataClass
    implements Insertable<OfflineWatchEventRow> {
  final String watchEventId;
  final String titleId;
  final String watchedAt;
  final double progressPercentage;
  final String? notes;
  final bool isTombstoned;
  const OfflineWatchEventRow({
    required this.watchEventId,
    required this.titleId,
    required this.watchedAt,
    required this.progressPercentage,
    this.notes,
    required this.isTombstoned,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['watch_event_id'] = Variable<String>(watchEventId);
    map['title_id'] = Variable<String>(titleId);
    map['watched_at'] = Variable<String>(watchedAt);
    map['progress_percentage'] = Variable<double>(progressPercentage);
    if (!nullToAbsent || notes != null) {
      map['notes'] = Variable<String>(notes);
    }
    map['is_tombstoned'] = Variable<bool>(isTombstoned);
    return map;
  }

  OfflineWatchEventsCompanion toCompanion(bool nullToAbsent) {
    return OfflineWatchEventsCompanion(
      watchEventId: Value(watchEventId),
      titleId: Value(titleId),
      watchedAt: Value(watchedAt),
      progressPercentage: Value(progressPercentage),
      notes: notes == null && nullToAbsent
          ? const Value.absent()
          : Value(notes),
      isTombstoned: Value(isTombstoned),
    );
  }

  factory OfflineWatchEventRow.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return OfflineWatchEventRow(
      watchEventId: serializer.fromJson<String>(json['watchEventId']),
      titleId: serializer.fromJson<String>(json['titleId']),
      watchedAt: serializer.fromJson<String>(json['watchedAt']),
      progressPercentage: serializer.fromJson<double>(
        json['progressPercentage'],
      ),
      notes: serializer.fromJson<String?>(json['notes']),
      isTombstoned: serializer.fromJson<bool>(json['isTombstoned']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'watchEventId': serializer.toJson<String>(watchEventId),
      'titleId': serializer.toJson<String>(titleId),
      'watchedAt': serializer.toJson<String>(watchedAt),
      'progressPercentage': serializer.toJson<double>(progressPercentage),
      'notes': serializer.toJson<String?>(notes),
      'isTombstoned': serializer.toJson<bool>(isTombstoned),
    };
  }

  OfflineWatchEventRow copyWith({
    String? watchEventId,
    String? titleId,
    String? watchedAt,
    double? progressPercentage,
    Value<String?> notes = const Value.absent(),
    bool? isTombstoned,
  }) => OfflineWatchEventRow(
    watchEventId: watchEventId ?? this.watchEventId,
    titleId: titleId ?? this.titleId,
    watchedAt: watchedAt ?? this.watchedAt,
    progressPercentage: progressPercentage ?? this.progressPercentage,
    notes: notes.present ? notes.value : this.notes,
    isTombstoned: isTombstoned ?? this.isTombstoned,
  );
  OfflineWatchEventRow copyWithCompanion(OfflineWatchEventsCompanion data) {
    return OfflineWatchEventRow(
      watchEventId: data.watchEventId.present
          ? data.watchEventId.value
          : this.watchEventId,
      titleId: data.titleId.present ? data.titleId.value : this.titleId,
      watchedAt: data.watchedAt.present ? data.watchedAt.value : this.watchedAt,
      progressPercentage: data.progressPercentage.present
          ? data.progressPercentage.value
          : this.progressPercentage,
      notes: data.notes.present ? data.notes.value : this.notes,
      isTombstoned: data.isTombstoned.present
          ? data.isTombstoned.value
          : this.isTombstoned,
    );
  }

  @override
  String toString() {
    return (StringBuffer('OfflineWatchEventRow(')
          ..write('watchEventId: $watchEventId, ')
          ..write('titleId: $titleId, ')
          ..write('watchedAt: $watchedAt, ')
          ..write('progressPercentage: $progressPercentage, ')
          ..write('notes: $notes, ')
          ..write('isTombstoned: $isTombstoned')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    watchEventId,
    titleId,
    watchedAt,
    progressPercentage,
    notes,
    isTombstoned,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is OfflineWatchEventRow &&
          other.watchEventId == this.watchEventId &&
          other.titleId == this.titleId &&
          other.watchedAt == this.watchedAt &&
          other.progressPercentage == this.progressPercentage &&
          other.notes == this.notes &&
          other.isTombstoned == this.isTombstoned);
}

class OfflineWatchEventsCompanion
    extends UpdateCompanion<OfflineWatchEventRow> {
  final Value<String> watchEventId;
  final Value<String> titleId;
  final Value<String> watchedAt;
  final Value<double> progressPercentage;
  final Value<String?> notes;
  final Value<bool> isTombstoned;
  final Value<int> rowid;
  const OfflineWatchEventsCompanion({
    this.watchEventId = const Value.absent(),
    this.titleId = const Value.absent(),
    this.watchedAt = const Value.absent(),
    this.progressPercentage = const Value.absent(),
    this.notes = const Value.absent(),
    this.isTombstoned = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  OfflineWatchEventsCompanion.insert({
    required String watchEventId,
    required String titleId,
    required String watchedAt,
    this.progressPercentage = const Value.absent(),
    this.notes = const Value.absent(),
    this.isTombstoned = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : watchEventId = Value(watchEventId),
       titleId = Value(titleId),
       watchedAt = Value(watchedAt);
  static Insertable<OfflineWatchEventRow> custom({
    Expression<String>? watchEventId,
    Expression<String>? titleId,
    Expression<String>? watchedAt,
    Expression<double>? progressPercentage,
    Expression<String>? notes,
    Expression<bool>? isTombstoned,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (watchEventId != null) 'watch_event_id': watchEventId,
      if (titleId != null) 'title_id': titleId,
      if (watchedAt != null) 'watched_at': watchedAt,
      if (progressPercentage != null) 'progress_percentage': progressPercentage,
      if (notes != null) 'notes': notes,
      if (isTombstoned != null) 'is_tombstoned': isTombstoned,
      if (rowid != null) 'rowid': rowid,
    });
  }

  OfflineWatchEventsCompanion copyWith({
    Value<String>? watchEventId,
    Value<String>? titleId,
    Value<String>? watchedAt,
    Value<double>? progressPercentage,
    Value<String?>? notes,
    Value<bool>? isTombstoned,
    Value<int>? rowid,
  }) {
    return OfflineWatchEventsCompanion(
      watchEventId: watchEventId ?? this.watchEventId,
      titleId: titleId ?? this.titleId,
      watchedAt: watchedAt ?? this.watchedAt,
      progressPercentage: progressPercentage ?? this.progressPercentage,
      notes: notes ?? this.notes,
      isTombstoned: isTombstoned ?? this.isTombstoned,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (watchEventId.present) {
      map['watch_event_id'] = Variable<String>(watchEventId.value);
    }
    if (titleId.present) {
      map['title_id'] = Variable<String>(titleId.value);
    }
    if (watchedAt.present) {
      map['watched_at'] = Variable<String>(watchedAt.value);
    }
    if (progressPercentage.present) {
      map['progress_percentage'] = Variable<double>(progressPercentage.value);
    }
    if (notes.present) {
      map['notes'] = Variable<String>(notes.value);
    }
    if (isTombstoned.present) {
      map['is_tombstoned'] = Variable<bool>(isTombstoned.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('OfflineWatchEventsCompanion(')
          ..write('watchEventId: $watchEventId, ')
          ..write('titleId: $titleId, ')
          ..write('watchedAt: $watchedAt, ')
          ..write('progressPercentage: $progressPercentage, ')
          ..write('notes: $notes, ')
          ..write('isTombstoned: $isTombstoned, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $OfflineRatingsTable extends OfflineRatings
    with TableInfo<$OfflineRatingsTable, OfflineRatingRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $OfflineRatingsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _ratingIdMeta = const VerificationMeta(
    'ratingId',
  );
  @override
  late final GeneratedColumn<String> ratingId = GeneratedColumn<String>(
    'rating_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _titleIdMeta = const VerificationMeta(
    'titleId',
  );
  @override
  late final GeneratedColumn<String> titleId = GeneratedColumn<String>(
    'title_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _ratingValueMeta = const VerificationMeta(
    'ratingValue',
  );
  @override
  late final GeneratedColumn<int> ratingValue = GeneratedColumn<int>(
    'rating_value',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _ratedAtMeta = const VerificationMeta(
    'ratedAt',
  );
  @override
  late final GeneratedColumn<String> ratedAt = GeneratedColumn<String>(
    'rated_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    ratingId,
    titleId,
    ratingValue,
    ratedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'offline_ratings';
  @override
  VerificationContext validateIntegrity(
    Insertable<OfflineRatingRow> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('rating_id')) {
      context.handle(
        _ratingIdMeta,
        ratingId.isAcceptableOrUnknown(data['rating_id']!, _ratingIdMeta),
      );
    } else if (isInserting) {
      context.missing(_ratingIdMeta);
    }
    if (data.containsKey('title_id')) {
      context.handle(
        _titleIdMeta,
        titleId.isAcceptableOrUnknown(data['title_id']!, _titleIdMeta),
      );
    } else if (isInserting) {
      context.missing(_titleIdMeta);
    }
    if (data.containsKey('rating_value')) {
      context.handle(
        _ratingValueMeta,
        ratingValue.isAcceptableOrUnknown(
          data['rating_value']!,
          _ratingValueMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_ratingValueMeta);
    }
    if (data.containsKey('rated_at')) {
      context.handle(
        _ratedAtMeta,
        ratedAt.isAcceptableOrUnknown(data['rated_at']!, _ratedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_ratedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {ratingId};
  @override
  OfflineRatingRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return OfflineRatingRow(
      ratingId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}rating_id'],
      )!,
      titleId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}title_id'],
      )!,
      ratingValue: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}rating_value'],
      )!,
      ratedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}rated_at'],
      )!,
    );
  }

  @override
  $OfflineRatingsTable createAlias(String alias) {
    return $OfflineRatingsTable(attachedDatabase, alias);
  }
}

class OfflineRatingRow extends DataClass
    implements Insertable<OfflineRatingRow> {
  final String ratingId;
  final String titleId;
  final int ratingValue;
  final String ratedAt;
  const OfflineRatingRow({
    required this.ratingId,
    required this.titleId,
    required this.ratingValue,
    required this.ratedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['rating_id'] = Variable<String>(ratingId);
    map['title_id'] = Variable<String>(titleId);
    map['rating_value'] = Variable<int>(ratingValue);
    map['rated_at'] = Variable<String>(ratedAt);
    return map;
  }

  OfflineRatingsCompanion toCompanion(bool nullToAbsent) {
    return OfflineRatingsCompanion(
      ratingId: Value(ratingId),
      titleId: Value(titleId),
      ratingValue: Value(ratingValue),
      ratedAt: Value(ratedAt),
    );
  }

  factory OfflineRatingRow.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return OfflineRatingRow(
      ratingId: serializer.fromJson<String>(json['ratingId']),
      titleId: serializer.fromJson<String>(json['titleId']),
      ratingValue: serializer.fromJson<int>(json['ratingValue']),
      ratedAt: serializer.fromJson<String>(json['ratedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'ratingId': serializer.toJson<String>(ratingId),
      'titleId': serializer.toJson<String>(titleId),
      'ratingValue': serializer.toJson<int>(ratingValue),
      'ratedAt': serializer.toJson<String>(ratedAt),
    };
  }

  OfflineRatingRow copyWith({
    String? ratingId,
    String? titleId,
    int? ratingValue,
    String? ratedAt,
  }) => OfflineRatingRow(
    ratingId: ratingId ?? this.ratingId,
    titleId: titleId ?? this.titleId,
    ratingValue: ratingValue ?? this.ratingValue,
    ratedAt: ratedAt ?? this.ratedAt,
  );
  OfflineRatingRow copyWithCompanion(OfflineRatingsCompanion data) {
    return OfflineRatingRow(
      ratingId: data.ratingId.present ? data.ratingId.value : this.ratingId,
      titleId: data.titleId.present ? data.titleId.value : this.titleId,
      ratingValue: data.ratingValue.present
          ? data.ratingValue.value
          : this.ratingValue,
      ratedAt: data.ratedAt.present ? data.ratedAt.value : this.ratedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('OfflineRatingRow(')
          ..write('ratingId: $ratingId, ')
          ..write('titleId: $titleId, ')
          ..write('ratingValue: $ratingValue, ')
          ..write('ratedAt: $ratedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(ratingId, titleId, ratingValue, ratedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is OfflineRatingRow &&
          other.ratingId == this.ratingId &&
          other.titleId == this.titleId &&
          other.ratingValue == this.ratingValue &&
          other.ratedAt == this.ratedAt);
}

class OfflineRatingsCompanion extends UpdateCompanion<OfflineRatingRow> {
  final Value<String> ratingId;
  final Value<String> titleId;
  final Value<int> ratingValue;
  final Value<String> ratedAt;
  final Value<int> rowid;
  const OfflineRatingsCompanion({
    this.ratingId = const Value.absent(),
    this.titleId = const Value.absent(),
    this.ratingValue = const Value.absent(),
    this.ratedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  OfflineRatingsCompanion.insert({
    required String ratingId,
    required String titleId,
    required int ratingValue,
    required String ratedAt,
    this.rowid = const Value.absent(),
  }) : ratingId = Value(ratingId),
       titleId = Value(titleId),
       ratingValue = Value(ratingValue),
       ratedAt = Value(ratedAt);
  static Insertable<OfflineRatingRow> custom({
    Expression<String>? ratingId,
    Expression<String>? titleId,
    Expression<int>? ratingValue,
    Expression<String>? ratedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (ratingId != null) 'rating_id': ratingId,
      if (titleId != null) 'title_id': titleId,
      if (ratingValue != null) 'rating_value': ratingValue,
      if (ratedAt != null) 'rated_at': ratedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  OfflineRatingsCompanion copyWith({
    Value<String>? ratingId,
    Value<String>? titleId,
    Value<int>? ratingValue,
    Value<String>? ratedAt,
    Value<int>? rowid,
  }) {
    return OfflineRatingsCompanion(
      ratingId: ratingId ?? this.ratingId,
      titleId: titleId ?? this.titleId,
      ratingValue: ratingValue ?? this.ratingValue,
      ratedAt: ratedAt ?? this.ratedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (ratingId.present) {
      map['rating_id'] = Variable<String>(ratingId.value);
    }
    if (titleId.present) {
      map['title_id'] = Variable<String>(titleId.value);
    }
    if (ratingValue.present) {
      map['rating_value'] = Variable<int>(ratingValue.value);
    }
    if (ratedAt.present) {
      map['rated_at'] = Variable<String>(ratedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('OfflineRatingsCompanion(')
          ..write('ratingId: $ratingId, ')
          ..write('titleId: $titleId, ')
          ..write('ratingValue: $ratingValue, ')
          ..write('ratedAt: $ratedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $OfflineUserTitleStatesTable extends OfflineUserTitleStates
    with TableInfo<$OfflineUserTitleStatesTable, OfflineUserTitleStateRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $OfflineUserTitleStatesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _titleIdMeta = const VerificationMeta(
    'titleId',
  );
  @override
  late final GeneratedColumn<String> titleId = GeneratedColumn<String>(
    'title_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _manualStatusOverrideMeta =
      const VerificationMeta('manualStatusOverride');
  @override
  late final GeneratedColumn<String> manualStatusOverride =
      GeneratedColumn<String>(
        'manual_status_override',
        aliasedName,
        true,
        type: DriftSqlType.string,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _isFavoriteMeta = const VerificationMeta(
    'isFavorite',
  );
  @override
  late final GeneratedColumn<bool> isFavorite = GeneratedColumn<bool>(
    'is_favorite',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_favorite" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<String> updatedAt = GeneratedColumn<String>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    titleId,
    manualStatusOverride,
    isFavorite,
    updatedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'offline_user_title_states';
  @override
  VerificationContext validateIntegrity(
    Insertable<OfflineUserTitleStateRow> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('title_id')) {
      context.handle(
        _titleIdMeta,
        titleId.isAcceptableOrUnknown(data['title_id']!, _titleIdMeta),
      );
    } else if (isInserting) {
      context.missing(_titleIdMeta);
    }
    if (data.containsKey('manual_status_override')) {
      context.handle(
        _manualStatusOverrideMeta,
        manualStatusOverride.isAcceptableOrUnknown(
          data['manual_status_override']!,
          _manualStatusOverrideMeta,
        ),
      );
    }
    if (data.containsKey('is_favorite')) {
      context.handle(
        _isFavoriteMeta,
        isFavorite.isAcceptableOrUnknown(data['is_favorite']!, _isFavoriteMeta),
      );
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {titleId};
  @override
  OfflineUserTitleStateRow map(
    Map<String, dynamic> data, {
    String? tablePrefix,
  }) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return OfflineUserTitleStateRow(
      titleId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}title_id'],
      )!,
      manualStatusOverride: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}manual_status_override'],
      ),
      isFavorite: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_favorite'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}updated_at'],
      )!,
    );
  }

  @override
  $OfflineUserTitleStatesTable createAlias(String alias) {
    return $OfflineUserTitleStatesTable(attachedDatabase, alias);
  }
}

class OfflineUserTitleStateRow extends DataClass
    implements Insertable<OfflineUserTitleStateRow> {
  final String titleId;
  final String? manualStatusOverride;
  final bool isFavorite;
  final String updatedAt;
  const OfflineUserTitleStateRow({
    required this.titleId,
    this.manualStatusOverride,
    required this.isFavorite,
    required this.updatedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['title_id'] = Variable<String>(titleId);
    if (!nullToAbsent || manualStatusOverride != null) {
      map['manual_status_override'] = Variable<String>(manualStatusOverride);
    }
    map['is_favorite'] = Variable<bool>(isFavorite);
    map['updated_at'] = Variable<String>(updatedAt);
    return map;
  }

  OfflineUserTitleStatesCompanion toCompanion(bool nullToAbsent) {
    return OfflineUserTitleStatesCompanion(
      titleId: Value(titleId),
      manualStatusOverride: manualStatusOverride == null && nullToAbsent
          ? const Value.absent()
          : Value(manualStatusOverride),
      isFavorite: Value(isFavorite),
      updatedAt: Value(updatedAt),
    );
  }

  factory OfflineUserTitleStateRow.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return OfflineUserTitleStateRow(
      titleId: serializer.fromJson<String>(json['titleId']),
      manualStatusOverride: serializer.fromJson<String?>(
        json['manualStatusOverride'],
      ),
      isFavorite: serializer.fromJson<bool>(json['isFavorite']),
      updatedAt: serializer.fromJson<String>(json['updatedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'titleId': serializer.toJson<String>(titleId),
      'manualStatusOverride': serializer.toJson<String?>(manualStatusOverride),
      'isFavorite': serializer.toJson<bool>(isFavorite),
      'updatedAt': serializer.toJson<String>(updatedAt),
    };
  }

  OfflineUserTitleStateRow copyWith({
    String? titleId,
    Value<String?> manualStatusOverride = const Value.absent(),
    bool? isFavorite,
    String? updatedAt,
  }) => OfflineUserTitleStateRow(
    titleId: titleId ?? this.titleId,
    manualStatusOverride: manualStatusOverride.present
        ? manualStatusOverride.value
        : this.manualStatusOverride,
    isFavorite: isFavorite ?? this.isFavorite,
    updatedAt: updatedAt ?? this.updatedAt,
  );
  OfflineUserTitleStateRow copyWithCompanion(
    OfflineUserTitleStatesCompanion data,
  ) {
    return OfflineUserTitleStateRow(
      titleId: data.titleId.present ? data.titleId.value : this.titleId,
      manualStatusOverride: data.manualStatusOverride.present
          ? data.manualStatusOverride.value
          : this.manualStatusOverride,
      isFavorite: data.isFavorite.present
          ? data.isFavorite.value
          : this.isFavorite,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('OfflineUserTitleStateRow(')
          ..write('titleId: $titleId, ')
          ..write('manualStatusOverride: $manualStatusOverride, ')
          ..write('isFavorite: $isFavorite, ')
          ..write('updatedAt: $updatedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(titleId, manualStatusOverride, isFavorite, updatedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is OfflineUserTitleStateRow &&
          other.titleId == this.titleId &&
          other.manualStatusOverride == this.manualStatusOverride &&
          other.isFavorite == this.isFavorite &&
          other.updatedAt == this.updatedAt);
}

class OfflineUserTitleStatesCompanion
    extends UpdateCompanion<OfflineUserTitleStateRow> {
  final Value<String> titleId;
  final Value<String?> manualStatusOverride;
  final Value<bool> isFavorite;
  final Value<String> updatedAt;
  final Value<int> rowid;
  const OfflineUserTitleStatesCompanion({
    this.titleId = const Value.absent(),
    this.manualStatusOverride = const Value.absent(),
    this.isFavorite = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  OfflineUserTitleStatesCompanion.insert({
    required String titleId,
    this.manualStatusOverride = const Value.absent(),
    this.isFavorite = const Value.absent(),
    required String updatedAt,
    this.rowid = const Value.absent(),
  }) : titleId = Value(titleId),
       updatedAt = Value(updatedAt);
  static Insertable<OfflineUserTitleStateRow> custom({
    Expression<String>? titleId,
    Expression<String>? manualStatusOverride,
    Expression<bool>? isFavorite,
    Expression<String>? updatedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (titleId != null) 'title_id': titleId,
      if (manualStatusOverride != null)
        'manual_status_override': manualStatusOverride,
      if (isFavorite != null) 'is_favorite': isFavorite,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  OfflineUserTitleStatesCompanion copyWith({
    Value<String>? titleId,
    Value<String?>? manualStatusOverride,
    Value<bool>? isFavorite,
    Value<String>? updatedAt,
    Value<int>? rowid,
  }) {
    return OfflineUserTitleStatesCompanion(
      titleId: titleId ?? this.titleId,
      manualStatusOverride: manualStatusOverride ?? this.manualStatusOverride,
      isFavorite: isFavorite ?? this.isFavorite,
      updatedAt: updatedAt ?? this.updatedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (titleId.present) {
      map['title_id'] = Variable<String>(titleId.value);
    }
    if (manualStatusOverride.present) {
      map['manual_status_override'] = Variable<String>(
        manualStatusOverride.value,
      );
    }
    if (isFavorite.present) {
      map['is_favorite'] = Variable<bool>(isFavorite.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<String>(updatedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('OfflineUserTitleStatesCompanion(')
          ..write('titleId: $titleId, ')
          ..write('manualStatusOverride: $manualStatusOverride, ')
          ..write('isFavorite: $isFavorite, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $OfflineNotesTable extends OfflineNotes
    with TableInfo<$OfflineNotesTable, OfflineNoteRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $OfflineNotesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _noteIdMeta = const VerificationMeta('noteId');
  @override
  late final GeneratedColumn<String> noteId = GeneratedColumn<String>(
    'note_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _titleIdMeta = const VerificationMeta(
    'titleId',
  );
  @override
  late final GeneratedColumn<String> titleId = GeneratedColumn<String>(
    'title_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _noteTextMeta = const VerificationMeta(
    'noteText',
  );
  @override
  late final GeneratedColumn<String> noteText = GeneratedColumn<String>(
    'note_text',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<String> updatedAt = GeneratedColumn<String>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [noteId, titleId, noteText, updatedAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'offline_notes';
  @override
  VerificationContext validateIntegrity(
    Insertable<OfflineNoteRow> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('note_id')) {
      context.handle(
        _noteIdMeta,
        noteId.isAcceptableOrUnknown(data['note_id']!, _noteIdMeta),
      );
    } else if (isInserting) {
      context.missing(_noteIdMeta);
    }
    if (data.containsKey('title_id')) {
      context.handle(
        _titleIdMeta,
        titleId.isAcceptableOrUnknown(data['title_id']!, _titleIdMeta),
      );
    } else if (isInserting) {
      context.missing(_titleIdMeta);
    }
    if (data.containsKey('note_text')) {
      context.handle(
        _noteTextMeta,
        noteText.isAcceptableOrUnknown(data['note_text']!, _noteTextMeta),
      );
    } else if (isInserting) {
      context.missing(_noteTextMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {noteId};
  @override
  OfflineNoteRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return OfflineNoteRow(
      noteId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}note_id'],
      )!,
      titleId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}title_id'],
      )!,
      noteText: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}note_text'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}updated_at'],
      )!,
    );
  }

  @override
  $OfflineNotesTable createAlias(String alias) {
    return $OfflineNotesTable(attachedDatabase, alias);
  }
}

class OfflineNoteRow extends DataClass implements Insertable<OfflineNoteRow> {
  final String noteId;
  final String titleId;
  final String noteText;
  final String updatedAt;
  const OfflineNoteRow({
    required this.noteId,
    required this.titleId,
    required this.noteText,
    required this.updatedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['note_id'] = Variable<String>(noteId);
    map['title_id'] = Variable<String>(titleId);
    map['note_text'] = Variable<String>(noteText);
    map['updated_at'] = Variable<String>(updatedAt);
    return map;
  }

  OfflineNotesCompanion toCompanion(bool nullToAbsent) {
    return OfflineNotesCompanion(
      noteId: Value(noteId),
      titleId: Value(titleId),
      noteText: Value(noteText),
      updatedAt: Value(updatedAt),
    );
  }

  factory OfflineNoteRow.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return OfflineNoteRow(
      noteId: serializer.fromJson<String>(json['noteId']),
      titleId: serializer.fromJson<String>(json['titleId']),
      noteText: serializer.fromJson<String>(json['noteText']),
      updatedAt: serializer.fromJson<String>(json['updatedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'noteId': serializer.toJson<String>(noteId),
      'titleId': serializer.toJson<String>(titleId),
      'noteText': serializer.toJson<String>(noteText),
      'updatedAt': serializer.toJson<String>(updatedAt),
    };
  }

  OfflineNoteRow copyWith({
    String? noteId,
    String? titleId,
    String? noteText,
    String? updatedAt,
  }) => OfflineNoteRow(
    noteId: noteId ?? this.noteId,
    titleId: titleId ?? this.titleId,
    noteText: noteText ?? this.noteText,
    updatedAt: updatedAt ?? this.updatedAt,
  );
  OfflineNoteRow copyWithCompanion(OfflineNotesCompanion data) {
    return OfflineNoteRow(
      noteId: data.noteId.present ? data.noteId.value : this.noteId,
      titleId: data.titleId.present ? data.titleId.value : this.titleId,
      noteText: data.noteText.present ? data.noteText.value : this.noteText,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('OfflineNoteRow(')
          ..write('noteId: $noteId, ')
          ..write('titleId: $titleId, ')
          ..write('noteText: $noteText, ')
          ..write('updatedAt: $updatedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(noteId, titleId, noteText, updatedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is OfflineNoteRow &&
          other.noteId == this.noteId &&
          other.titleId == this.titleId &&
          other.noteText == this.noteText &&
          other.updatedAt == this.updatedAt);
}

class OfflineNotesCompanion extends UpdateCompanion<OfflineNoteRow> {
  final Value<String> noteId;
  final Value<String> titleId;
  final Value<String> noteText;
  final Value<String> updatedAt;
  final Value<int> rowid;
  const OfflineNotesCompanion({
    this.noteId = const Value.absent(),
    this.titleId = const Value.absent(),
    this.noteText = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  OfflineNotesCompanion.insert({
    required String noteId,
    required String titleId,
    required String noteText,
    required String updatedAt,
    this.rowid = const Value.absent(),
  }) : noteId = Value(noteId),
       titleId = Value(titleId),
       noteText = Value(noteText),
       updatedAt = Value(updatedAt);
  static Insertable<OfflineNoteRow> custom({
    Expression<String>? noteId,
    Expression<String>? titleId,
    Expression<String>? noteText,
    Expression<String>? updatedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (noteId != null) 'note_id': noteId,
      if (titleId != null) 'title_id': titleId,
      if (noteText != null) 'note_text': noteText,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  OfflineNotesCompanion copyWith({
    Value<String>? noteId,
    Value<String>? titleId,
    Value<String>? noteText,
    Value<String>? updatedAt,
    Value<int>? rowid,
  }) {
    return OfflineNotesCompanion(
      noteId: noteId ?? this.noteId,
      titleId: titleId ?? this.titleId,
      noteText: noteText ?? this.noteText,
      updatedAt: updatedAt ?? this.updatedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (noteId.present) {
      map['note_id'] = Variable<String>(noteId.value);
    }
    if (titleId.present) {
      map['title_id'] = Variable<String>(titleId.value);
    }
    if (noteText.present) {
      map['note_text'] = Variable<String>(noteText.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<String>(updatedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('OfflineNotesCompanion(')
          ..write('noteId: $noteId, ')
          ..write('titleId: $titleId, ')
          ..write('noteText: $noteText, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $OutboxMutationsTable outboxMutations = $OutboxMutationsTable(
    this,
  );
  late final $CachedTitlesTable cachedTitles = $CachedTitlesTable(this);
  late final $OfflineWatchEventsTable offlineWatchEvents =
      $OfflineWatchEventsTable(this);
  late final $OfflineRatingsTable offlineRatings = $OfflineRatingsTable(this);
  late final $OfflineUserTitleStatesTable offlineUserTitleStates =
      $OfflineUserTitleStatesTable(this);
  late final $OfflineNotesTable offlineNotes = $OfflineNotesTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    outboxMutations,
    cachedTitles,
    offlineWatchEvents,
    offlineRatings,
    offlineUserTitleStates,
    offlineNotes,
  ];
}

typedef $$OutboxMutationsTableCreateCompanionBuilder =
    OutboxMutationsCompanion Function({
      required String mutationId,
      required String mutationType,
      required String clientTimestamp,
      required String payloadJson,
      Value<String> status,
      Value<int> retryCount,
      Value<int> rowid,
    });
typedef $$OutboxMutationsTableUpdateCompanionBuilder =
    OutboxMutationsCompanion Function({
      Value<String> mutationId,
      Value<String> mutationType,
      Value<String> clientTimestamp,
      Value<String> payloadJson,
      Value<String> status,
      Value<int> retryCount,
      Value<int> rowid,
    });

class $$OutboxMutationsTableFilterComposer
    extends Composer<_$AppDatabase, $OutboxMutationsTable> {
  $$OutboxMutationsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get mutationId => $composableBuilder(
    column: $table.mutationId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get mutationType => $composableBuilder(
    column: $table.mutationType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get clientTimestamp => $composableBuilder(
    column: $table.clientTimestamp,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get payloadJson => $composableBuilder(
    column: $table.payloadJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get retryCount => $composableBuilder(
    column: $table.retryCount,
    builder: (column) => ColumnFilters(column),
  );
}

class $$OutboxMutationsTableOrderingComposer
    extends Composer<_$AppDatabase, $OutboxMutationsTable> {
  $$OutboxMutationsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get mutationId => $composableBuilder(
    column: $table.mutationId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get mutationType => $composableBuilder(
    column: $table.mutationType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get clientTimestamp => $composableBuilder(
    column: $table.clientTimestamp,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get payloadJson => $composableBuilder(
    column: $table.payloadJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get retryCount => $composableBuilder(
    column: $table.retryCount,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$OutboxMutationsTableAnnotationComposer
    extends Composer<_$AppDatabase, $OutboxMutationsTable> {
  $$OutboxMutationsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get mutationId => $composableBuilder(
    column: $table.mutationId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get mutationType => $composableBuilder(
    column: $table.mutationType,
    builder: (column) => column,
  );

  GeneratedColumn<String> get clientTimestamp => $composableBuilder(
    column: $table.clientTimestamp,
    builder: (column) => column,
  );

  GeneratedColumn<String> get payloadJson => $composableBuilder(
    column: $table.payloadJson,
    builder: (column) => column,
  );

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<int> get retryCount => $composableBuilder(
    column: $table.retryCount,
    builder: (column) => column,
  );
}

class $$OutboxMutationsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $OutboxMutationsTable,
          OutboxMutationRow,
          $$OutboxMutationsTableFilterComposer,
          $$OutboxMutationsTableOrderingComposer,
          $$OutboxMutationsTableAnnotationComposer,
          $$OutboxMutationsTableCreateCompanionBuilder,
          $$OutboxMutationsTableUpdateCompanionBuilder,
          (
            OutboxMutationRow,
            BaseReferences<
              _$AppDatabase,
              $OutboxMutationsTable,
              OutboxMutationRow
            >,
          ),
          OutboxMutationRow,
          PrefetchHooks Function()
        > {
  $$OutboxMutationsTableTableManager(
    _$AppDatabase db,
    $OutboxMutationsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$OutboxMutationsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$OutboxMutationsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$OutboxMutationsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> mutationId = const Value.absent(),
                Value<String> mutationType = const Value.absent(),
                Value<String> clientTimestamp = const Value.absent(),
                Value<String> payloadJson = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<int> retryCount = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => OutboxMutationsCompanion(
                mutationId: mutationId,
                mutationType: mutationType,
                clientTimestamp: clientTimestamp,
                payloadJson: payloadJson,
                status: status,
                retryCount: retryCount,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String mutationId,
                required String mutationType,
                required String clientTimestamp,
                required String payloadJson,
                Value<String> status = const Value.absent(),
                Value<int> retryCount = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => OutboxMutationsCompanion.insert(
                mutationId: mutationId,
                mutationType: mutationType,
                clientTimestamp: clientTimestamp,
                payloadJson: payloadJson,
                status: status,
                retryCount: retryCount,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$OutboxMutationsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $OutboxMutationsTable,
      OutboxMutationRow,
      $$OutboxMutationsTableFilterComposer,
      $$OutboxMutationsTableOrderingComposer,
      $$OutboxMutationsTableAnnotationComposer,
      $$OutboxMutationsTableCreateCompanionBuilder,
      $$OutboxMutationsTableUpdateCompanionBuilder,
      (
        OutboxMutationRow,
        BaseReferences<_$AppDatabase, $OutboxMutationsTable, OutboxMutationRow>,
      ),
      OutboxMutationRow,
      PrefetchHooks Function()
    >;
typedef $$CachedTitlesTableCreateCompanionBuilder =
    CachedTitlesCompanion Function({
      required String titleId,
      required String displayId,
      required String primaryTitle,
      required String contentType,
      Value<int?> releaseYear,
      Value<String?> posterUrl,
      required String genresJson,
      required String cachedAt,
      Value<bool> isAuthoritative,
      Value<int> rowid,
    });
typedef $$CachedTitlesTableUpdateCompanionBuilder =
    CachedTitlesCompanion Function({
      Value<String> titleId,
      Value<String> displayId,
      Value<String> primaryTitle,
      Value<String> contentType,
      Value<int?> releaseYear,
      Value<String?> posterUrl,
      Value<String> genresJson,
      Value<String> cachedAt,
      Value<bool> isAuthoritative,
      Value<int> rowid,
    });

class $$CachedTitlesTableFilterComposer
    extends Composer<_$AppDatabase, $CachedTitlesTable> {
  $$CachedTitlesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get titleId => $composableBuilder(
    column: $table.titleId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get displayId => $composableBuilder(
    column: $table.displayId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get primaryTitle => $composableBuilder(
    column: $table.primaryTitle,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get contentType => $composableBuilder(
    column: $table.contentType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get releaseYear => $composableBuilder(
    column: $table.releaseYear,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get posterUrl => $composableBuilder(
    column: $table.posterUrl,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get genresJson => $composableBuilder(
    column: $table.genresJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get cachedAt => $composableBuilder(
    column: $table.cachedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isAuthoritative => $composableBuilder(
    column: $table.isAuthoritative,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedTitlesTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedTitlesTable> {
  $$CachedTitlesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get titleId => $composableBuilder(
    column: $table.titleId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get displayId => $composableBuilder(
    column: $table.displayId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get primaryTitle => $composableBuilder(
    column: $table.primaryTitle,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get contentType => $composableBuilder(
    column: $table.contentType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get releaseYear => $composableBuilder(
    column: $table.releaseYear,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get posterUrl => $composableBuilder(
    column: $table.posterUrl,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get genresJson => $composableBuilder(
    column: $table.genresJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get cachedAt => $composableBuilder(
    column: $table.cachedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isAuthoritative => $composableBuilder(
    column: $table.isAuthoritative,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedTitlesTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedTitlesTable> {
  $$CachedTitlesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get titleId =>
      $composableBuilder(column: $table.titleId, builder: (column) => column);

  GeneratedColumn<String> get displayId =>
      $composableBuilder(column: $table.displayId, builder: (column) => column);

  GeneratedColumn<String> get primaryTitle => $composableBuilder(
    column: $table.primaryTitle,
    builder: (column) => column,
  );

  GeneratedColumn<String> get contentType => $composableBuilder(
    column: $table.contentType,
    builder: (column) => column,
  );

  GeneratedColumn<int> get releaseYear => $composableBuilder(
    column: $table.releaseYear,
    builder: (column) => column,
  );

  GeneratedColumn<String> get posterUrl =>
      $composableBuilder(column: $table.posterUrl, builder: (column) => column);

  GeneratedColumn<String> get genresJson => $composableBuilder(
    column: $table.genresJson,
    builder: (column) => column,
  );

  GeneratedColumn<String> get cachedAt =>
      $composableBuilder(column: $table.cachedAt, builder: (column) => column);

  GeneratedColumn<bool> get isAuthoritative => $composableBuilder(
    column: $table.isAuthoritative,
    builder: (column) => column,
  );
}

class $$CachedTitlesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CachedTitlesTable,
          CachedTitleRow,
          $$CachedTitlesTableFilterComposer,
          $$CachedTitlesTableOrderingComposer,
          $$CachedTitlesTableAnnotationComposer,
          $$CachedTitlesTableCreateCompanionBuilder,
          $$CachedTitlesTableUpdateCompanionBuilder,
          (
            CachedTitleRow,
            BaseReferences<_$AppDatabase, $CachedTitlesTable, CachedTitleRow>,
          ),
          CachedTitleRow,
          PrefetchHooks Function()
        > {
  $$CachedTitlesTableTableManager(_$AppDatabase db, $CachedTitlesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedTitlesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedTitlesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedTitlesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> titleId = const Value.absent(),
                Value<String> displayId = const Value.absent(),
                Value<String> primaryTitle = const Value.absent(),
                Value<String> contentType = const Value.absent(),
                Value<int?> releaseYear = const Value.absent(),
                Value<String?> posterUrl = const Value.absent(),
                Value<String> genresJson = const Value.absent(),
                Value<String> cachedAt = const Value.absent(),
                Value<bool> isAuthoritative = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedTitlesCompanion(
                titleId: titleId,
                displayId: displayId,
                primaryTitle: primaryTitle,
                contentType: contentType,
                releaseYear: releaseYear,
                posterUrl: posterUrl,
                genresJson: genresJson,
                cachedAt: cachedAt,
                isAuthoritative: isAuthoritative,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String titleId,
                required String displayId,
                required String primaryTitle,
                required String contentType,
                Value<int?> releaseYear = const Value.absent(),
                Value<String?> posterUrl = const Value.absent(),
                required String genresJson,
                required String cachedAt,
                Value<bool> isAuthoritative = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedTitlesCompanion.insert(
                titleId: titleId,
                displayId: displayId,
                primaryTitle: primaryTitle,
                contentType: contentType,
                releaseYear: releaseYear,
                posterUrl: posterUrl,
                genresJson: genresJson,
                cachedAt: cachedAt,
                isAuthoritative: isAuthoritative,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedTitlesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CachedTitlesTable,
      CachedTitleRow,
      $$CachedTitlesTableFilterComposer,
      $$CachedTitlesTableOrderingComposer,
      $$CachedTitlesTableAnnotationComposer,
      $$CachedTitlesTableCreateCompanionBuilder,
      $$CachedTitlesTableUpdateCompanionBuilder,
      (
        CachedTitleRow,
        BaseReferences<_$AppDatabase, $CachedTitlesTable, CachedTitleRow>,
      ),
      CachedTitleRow,
      PrefetchHooks Function()
    >;
typedef $$OfflineWatchEventsTableCreateCompanionBuilder =
    OfflineWatchEventsCompanion Function({
      required String watchEventId,
      required String titleId,
      required String watchedAt,
      Value<double> progressPercentage,
      Value<String?> notes,
      Value<bool> isTombstoned,
      Value<int> rowid,
    });
typedef $$OfflineWatchEventsTableUpdateCompanionBuilder =
    OfflineWatchEventsCompanion Function({
      Value<String> watchEventId,
      Value<String> titleId,
      Value<String> watchedAt,
      Value<double> progressPercentage,
      Value<String?> notes,
      Value<bool> isTombstoned,
      Value<int> rowid,
    });

class $$OfflineWatchEventsTableFilterComposer
    extends Composer<_$AppDatabase, $OfflineWatchEventsTable> {
  $$OfflineWatchEventsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get watchEventId => $composableBuilder(
    column: $table.watchEventId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get titleId => $composableBuilder(
    column: $table.titleId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get watchedAt => $composableBuilder(
    column: $table.watchedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get progressPercentage => $composableBuilder(
    column: $table.progressPercentage,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get notes => $composableBuilder(
    column: $table.notes,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isTombstoned => $composableBuilder(
    column: $table.isTombstoned,
    builder: (column) => ColumnFilters(column),
  );
}

class $$OfflineWatchEventsTableOrderingComposer
    extends Composer<_$AppDatabase, $OfflineWatchEventsTable> {
  $$OfflineWatchEventsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get watchEventId => $composableBuilder(
    column: $table.watchEventId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get titleId => $composableBuilder(
    column: $table.titleId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get watchedAt => $composableBuilder(
    column: $table.watchedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get progressPercentage => $composableBuilder(
    column: $table.progressPercentage,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get notes => $composableBuilder(
    column: $table.notes,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isTombstoned => $composableBuilder(
    column: $table.isTombstoned,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$OfflineWatchEventsTableAnnotationComposer
    extends Composer<_$AppDatabase, $OfflineWatchEventsTable> {
  $$OfflineWatchEventsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get watchEventId => $composableBuilder(
    column: $table.watchEventId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get titleId =>
      $composableBuilder(column: $table.titleId, builder: (column) => column);

  GeneratedColumn<String> get watchedAt =>
      $composableBuilder(column: $table.watchedAt, builder: (column) => column);

  GeneratedColumn<double> get progressPercentage => $composableBuilder(
    column: $table.progressPercentage,
    builder: (column) => column,
  );

  GeneratedColumn<String> get notes =>
      $composableBuilder(column: $table.notes, builder: (column) => column);

  GeneratedColumn<bool> get isTombstoned => $composableBuilder(
    column: $table.isTombstoned,
    builder: (column) => column,
  );
}

class $$OfflineWatchEventsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $OfflineWatchEventsTable,
          OfflineWatchEventRow,
          $$OfflineWatchEventsTableFilterComposer,
          $$OfflineWatchEventsTableOrderingComposer,
          $$OfflineWatchEventsTableAnnotationComposer,
          $$OfflineWatchEventsTableCreateCompanionBuilder,
          $$OfflineWatchEventsTableUpdateCompanionBuilder,
          (
            OfflineWatchEventRow,
            BaseReferences<
              _$AppDatabase,
              $OfflineWatchEventsTable,
              OfflineWatchEventRow
            >,
          ),
          OfflineWatchEventRow,
          PrefetchHooks Function()
        > {
  $$OfflineWatchEventsTableTableManager(
    _$AppDatabase db,
    $OfflineWatchEventsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$OfflineWatchEventsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$OfflineWatchEventsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$OfflineWatchEventsTableAnnotationComposer(
                $db: db,
                $table: table,
              ),
          updateCompanionCallback:
              ({
                Value<String> watchEventId = const Value.absent(),
                Value<String> titleId = const Value.absent(),
                Value<String> watchedAt = const Value.absent(),
                Value<double> progressPercentage = const Value.absent(),
                Value<String?> notes = const Value.absent(),
                Value<bool> isTombstoned = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => OfflineWatchEventsCompanion(
                watchEventId: watchEventId,
                titleId: titleId,
                watchedAt: watchedAt,
                progressPercentage: progressPercentage,
                notes: notes,
                isTombstoned: isTombstoned,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String watchEventId,
                required String titleId,
                required String watchedAt,
                Value<double> progressPercentage = const Value.absent(),
                Value<String?> notes = const Value.absent(),
                Value<bool> isTombstoned = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => OfflineWatchEventsCompanion.insert(
                watchEventId: watchEventId,
                titleId: titleId,
                watchedAt: watchedAt,
                progressPercentage: progressPercentage,
                notes: notes,
                isTombstoned: isTombstoned,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$OfflineWatchEventsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $OfflineWatchEventsTable,
      OfflineWatchEventRow,
      $$OfflineWatchEventsTableFilterComposer,
      $$OfflineWatchEventsTableOrderingComposer,
      $$OfflineWatchEventsTableAnnotationComposer,
      $$OfflineWatchEventsTableCreateCompanionBuilder,
      $$OfflineWatchEventsTableUpdateCompanionBuilder,
      (
        OfflineWatchEventRow,
        BaseReferences<
          _$AppDatabase,
          $OfflineWatchEventsTable,
          OfflineWatchEventRow
        >,
      ),
      OfflineWatchEventRow,
      PrefetchHooks Function()
    >;
typedef $$OfflineRatingsTableCreateCompanionBuilder =
    OfflineRatingsCompanion Function({
      required String ratingId,
      required String titleId,
      required int ratingValue,
      required String ratedAt,
      Value<int> rowid,
    });
typedef $$OfflineRatingsTableUpdateCompanionBuilder =
    OfflineRatingsCompanion Function({
      Value<String> ratingId,
      Value<String> titleId,
      Value<int> ratingValue,
      Value<String> ratedAt,
      Value<int> rowid,
    });

class $$OfflineRatingsTableFilterComposer
    extends Composer<_$AppDatabase, $OfflineRatingsTable> {
  $$OfflineRatingsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get ratingId => $composableBuilder(
    column: $table.ratingId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get titleId => $composableBuilder(
    column: $table.titleId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get ratingValue => $composableBuilder(
    column: $table.ratingValue,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get ratedAt => $composableBuilder(
    column: $table.ratedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$OfflineRatingsTableOrderingComposer
    extends Composer<_$AppDatabase, $OfflineRatingsTable> {
  $$OfflineRatingsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get ratingId => $composableBuilder(
    column: $table.ratingId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get titleId => $composableBuilder(
    column: $table.titleId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get ratingValue => $composableBuilder(
    column: $table.ratingValue,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get ratedAt => $composableBuilder(
    column: $table.ratedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$OfflineRatingsTableAnnotationComposer
    extends Composer<_$AppDatabase, $OfflineRatingsTable> {
  $$OfflineRatingsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get ratingId =>
      $composableBuilder(column: $table.ratingId, builder: (column) => column);

  GeneratedColumn<String> get titleId =>
      $composableBuilder(column: $table.titleId, builder: (column) => column);

  GeneratedColumn<int> get ratingValue => $composableBuilder(
    column: $table.ratingValue,
    builder: (column) => column,
  );

  GeneratedColumn<String> get ratedAt =>
      $composableBuilder(column: $table.ratedAt, builder: (column) => column);
}

class $$OfflineRatingsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $OfflineRatingsTable,
          OfflineRatingRow,
          $$OfflineRatingsTableFilterComposer,
          $$OfflineRatingsTableOrderingComposer,
          $$OfflineRatingsTableAnnotationComposer,
          $$OfflineRatingsTableCreateCompanionBuilder,
          $$OfflineRatingsTableUpdateCompanionBuilder,
          (
            OfflineRatingRow,
            BaseReferences<
              _$AppDatabase,
              $OfflineRatingsTable,
              OfflineRatingRow
            >,
          ),
          OfflineRatingRow,
          PrefetchHooks Function()
        > {
  $$OfflineRatingsTableTableManager(
    _$AppDatabase db,
    $OfflineRatingsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$OfflineRatingsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$OfflineRatingsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$OfflineRatingsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> ratingId = const Value.absent(),
                Value<String> titleId = const Value.absent(),
                Value<int> ratingValue = const Value.absent(),
                Value<String> ratedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => OfflineRatingsCompanion(
                ratingId: ratingId,
                titleId: titleId,
                ratingValue: ratingValue,
                ratedAt: ratedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String ratingId,
                required String titleId,
                required int ratingValue,
                required String ratedAt,
                Value<int> rowid = const Value.absent(),
              }) => OfflineRatingsCompanion.insert(
                ratingId: ratingId,
                titleId: titleId,
                ratingValue: ratingValue,
                ratedAt: ratedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$OfflineRatingsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $OfflineRatingsTable,
      OfflineRatingRow,
      $$OfflineRatingsTableFilterComposer,
      $$OfflineRatingsTableOrderingComposer,
      $$OfflineRatingsTableAnnotationComposer,
      $$OfflineRatingsTableCreateCompanionBuilder,
      $$OfflineRatingsTableUpdateCompanionBuilder,
      (
        OfflineRatingRow,
        BaseReferences<_$AppDatabase, $OfflineRatingsTable, OfflineRatingRow>,
      ),
      OfflineRatingRow,
      PrefetchHooks Function()
    >;
typedef $$OfflineUserTitleStatesTableCreateCompanionBuilder =
    OfflineUserTitleStatesCompanion Function({
      required String titleId,
      Value<String?> manualStatusOverride,
      Value<bool> isFavorite,
      required String updatedAt,
      Value<int> rowid,
    });
typedef $$OfflineUserTitleStatesTableUpdateCompanionBuilder =
    OfflineUserTitleStatesCompanion Function({
      Value<String> titleId,
      Value<String?> manualStatusOverride,
      Value<bool> isFavorite,
      Value<String> updatedAt,
      Value<int> rowid,
    });

class $$OfflineUserTitleStatesTableFilterComposer
    extends Composer<_$AppDatabase, $OfflineUserTitleStatesTable> {
  $$OfflineUserTitleStatesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get titleId => $composableBuilder(
    column: $table.titleId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get manualStatusOverride => $composableBuilder(
    column: $table.manualStatusOverride,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isFavorite => $composableBuilder(
    column: $table.isFavorite,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$OfflineUserTitleStatesTableOrderingComposer
    extends Composer<_$AppDatabase, $OfflineUserTitleStatesTable> {
  $$OfflineUserTitleStatesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get titleId => $composableBuilder(
    column: $table.titleId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get manualStatusOverride => $composableBuilder(
    column: $table.manualStatusOverride,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isFavorite => $composableBuilder(
    column: $table.isFavorite,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$OfflineUserTitleStatesTableAnnotationComposer
    extends Composer<_$AppDatabase, $OfflineUserTitleStatesTable> {
  $$OfflineUserTitleStatesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get titleId =>
      $composableBuilder(column: $table.titleId, builder: (column) => column);

  GeneratedColumn<String> get manualStatusOverride => $composableBuilder(
    column: $table.manualStatusOverride,
    builder: (column) => column,
  );

  GeneratedColumn<bool> get isFavorite => $composableBuilder(
    column: $table.isFavorite,
    builder: (column) => column,
  );

  GeneratedColumn<String> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);
}

class $$OfflineUserTitleStatesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $OfflineUserTitleStatesTable,
          OfflineUserTitleStateRow,
          $$OfflineUserTitleStatesTableFilterComposer,
          $$OfflineUserTitleStatesTableOrderingComposer,
          $$OfflineUserTitleStatesTableAnnotationComposer,
          $$OfflineUserTitleStatesTableCreateCompanionBuilder,
          $$OfflineUserTitleStatesTableUpdateCompanionBuilder,
          (
            OfflineUserTitleStateRow,
            BaseReferences<
              _$AppDatabase,
              $OfflineUserTitleStatesTable,
              OfflineUserTitleStateRow
            >,
          ),
          OfflineUserTitleStateRow,
          PrefetchHooks Function()
        > {
  $$OfflineUserTitleStatesTableTableManager(
    _$AppDatabase db,
    $OfflineUserTitleStatesTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$OfflineUserTitleStatesTableFilterComposer(
                $db: db,
                $table: table,
              ),
          createOrderingComposer: () =>
              $$OfflineUserTitleStatesTableOrderingComposer(
                $db: db,
                $table: table,
              ),
          createComputedFieldComposer: () =>
              $$OfflineUserTitleStatesTableAnnotationComposer(
                $db: db,
                $table: table,
              ),
          updateCompanionCallback:
              ({
                Value<String> titleId = const Value.absent(),
                Value<String?> manualStatusOverride = const Value.absent(),
                Value<bool> isFavorite = const Value.absent(),
                Value<String> updatedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => OfflineUserTitleStatesCompanion(
                titleId: titleId,
                manualStatusOverride: manualStatusOverride,
                isFavorite: isFavorite,
                updatedAt: updatedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String titleId,
                Value<String?> manualStatusOverride = const Value.absent(),
                Value<bool> isFavorite = const Value.absent(),
                required String updatedAt,
                Value<int> rowid = const Value.absent(),
              }) => OfflineUserTitleStatesCompanion.insert(
                titleId: titleId,
                manualStatusOverride: manualStatusOverride,
                isFavorite: isFavorite,
                updatedAt: updatedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$OfflineUserTitleStatesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $OfflineUserTitleStatesTable,
      OfflineUserTitleStateRow,
      $$OfflineUserTitleStatesTableFilterComposer,
      $$OfflineUserTitleStatesTableOrderingComposer,
      $$OfflineUserTitleStatesTableAnnotationComposer,
      $$OfflineUserTitleStatesTableCreateCompanionBuilder,
      $$OfflineUserTitleStatesTableUpdateCompanionBuilder,
      (
        OfflineUserTitleStateRow,
        BaseReferences<
          _$AppDatabase,
          $OfflineUserTitleStatesTable,
          OfflineUserTitleStateRow
        >,
      ),
      OfflineUserTitleStateRow,
      PrefetchHooks Function()
    >;
typedef $$OfflineNotesTableCreateCompanionBuilder =
    OfflineNotesCompanion Function({
      required String noteId,
      required String titleId,
      required String noteText,
      required String updatedAt,
      Value<int> rowid,
    });
typedef $$OfflineNotesTableUpdateCompanionBuilder =
    OfflineNotesCompanion Function({
      Value<String> noteId,
      Value<String> titleId,
      Value<String> noteText,
      Value<String> updatedAt,
      Value<int> rowid,
    });

class $$OfflineNotesTableFilterComposer
    extends Composer<_$AppDatabase, $OfflineNotesTable> {
  $$OfflineNotesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get noteId => $composableBuilder(
    column: $table.noteId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get titleId => $composableBuilder(
    column: $table.titleId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get noteText => $composableBuilder(
    column: $table.noteText,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$OfflineNotesTableOrderingComposer
    extends Composer<_$AppDatabase, $OfflineNotesTable> {
  $$OfflineNotesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get noteId => $composableBuilder(
    column: $table.noteId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get titleId => $composableBuilder(
    column: $table.titleId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get noteText => $composableBuilder(
    column: $table.noteText,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$OfflineNotesTableAnnotationComposer
    extends Composer<_$AppDatabase, $OfflineNotesTable> {
  $$OfflineNotesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get noteId =>
      $composableBuilder(column: $table.noteId, builder: (column) => column);

  GeneratedColumn<String> get titleId =>
      $composableBuilder(column: $table.titleId, builder: (column) => column);

  GeneratedColumn<String> get noteText =>
      $composableBuilder(column: $table.noteText, builder: (column) => column);

  GeneratedColumn<String> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);
}

class $$OfflineNotesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $OfflineNotesTable,
          OfflineNoteRow,
          $$OfflineNotesTableFilterComposer,
          $$OfflineNotesTableOrderingComposer,
          $$OfflineNotesTableAnnotationComposer,
          $$OfflineNotesTableCreateCompanionBuilder,
          $$OfflineNotesTableUpdateCompanionBuilder,
          (
            OfflineNoteRow,
            BaseReferences<_$AppDatabase, $OfflineNotesTable, OfflineNoteRow>,
          ),
          OfflineNoteRow,
          PrefetchHooks Function()
        > {
  $$OfflineNotesTableTableManager(_$AppDatabase db, $OfflineNotesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$OfflineNotesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$OfflineNotesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$OfflineNotesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> noteId = const Value.absent(),
                Value<String> titleId = const Value.absent(),
                Value<String> noteText = const Value.absent(),
                Value<String> updatedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => OfflineNotesCompanion(
                noteId: noteId,
                titleId: titleId,
                noteText: noteText,
                updatedAt: updatedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String noteId,
                required String titleId,
                required String noteText,
                required String updatedAt,
                Value<int> rowid = const Value.absent(),
              }) => OfflineNotesCompanion.insert(
                noteId: noteId,
                titleId: titleId,
                noteText: noteText,
                updatedAt: updatedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$OfflineNotesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $OfflineNotesTable,
      OfflineNoteRow,
      $$OfflineNotesTableFilterComposer,
      $$OfflineNotesTableOrderingComposer,
      $$OfflineNotesTableAnnotationComposer,
      $$OfflineNotesTableCreateCompanionBuilder,
      $$OfflineNotesTableUpdateCompanionBuilder,
      (
        OfflineNoteRow,
        BaseReferences<_$AppDatabase, $OfflineNotesTable, OfflineNoteRow>,
      ),
      OfflineNoteRow,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$OutboxMutationsTableTableManager get outboxMutations =>
      $$OutboxMutationsTableTableManager(_db, _db.outboxMutations);
  $$CachedTitlesTableTableManager get cachedTitles =>
      $$CachedTitlesTableTableManager(_db, _db.cachedTitles);
  $$OfflineWatchEventsTableTableManager get offlineWatchEvents =>
      $$OfflineWatchEventsTableTableManager(_db, _db.offlineWatchEvents);
  $$OfflineRatingsTableTableManager get offlineRatings =>
      $$OfflineRatingsTableTableManager(_db, _db.offlineRatings);
  $$OfflineUserTitleStatesTableTableManager get offlineUserTitleStates =>
      $$OfflineUserTitleStatesTableTableManager(
        _db,
        _db.offlineUserTitleStates,
      );
  $$OfflineNotesTableTableManager get offlineNotes =>
      $$OfflineNotesTableTableManager(_db, _db.offlineNotes);
}
