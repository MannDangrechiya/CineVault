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
  const CachedTitleRow({
    required this.titleId,
    required this.displayId,
    required this.primaryTitle,
    required this.contentType,
    this.releaseYear,
    this.posterUrl,
    required this.genresJson,
    required this.cachedAt,
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
  }) => CachedTitleRow(
    titleId: titleId ?? this.titleId,
    displayId: displayId ?? this.displayId,
    primaryTitle: primaryTitle ?? this.primaryTitle,
    contentType: contentType ?? this.contentType,
    releaseYear: releaseYear.present ? releaseYear.value : this.releaseYear,
    posterUrl: posterUrl.present ? posterUrl.value : this.posterUrl,
    genresJson: genresJson ?? this.genresJson,
    cachedAt: cachedAt ?? this.cachedAt,
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
          ..write('cachedAt: $cachedAt')
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
          other.cachedAt == this.cachedAt);
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
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $RecentSearchesTable extends RecentSearches
    with TableInfo<$RecentSearchesTable, RecentSearchRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $RecentSearchesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _queryMeta = const VerificationMeta('query');
  @override
  late final GeneratedColumn<String> query = GeneratedColumn<String>(
    'query',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _searchedAtMeta = const VerificationMeta(
    'searchedAt',
  );
  @override
  late final GeneratedColumn<String> searchedAt = GeneratedColumn<String>(
    'searched_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [query, searchedAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'recent_searches';
  @override
  VerificationContext validateIntegrity(
    Insertable<RecentSearchRow> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('query')) {
      context.handle(
        _queryMeta,
        query.isAcceptableOrUnknown(data['query']!, _queryMeta),
      );
    } else if (isInserting) {
      context.missing(_queryMeta);
    }
    if (data.containsKey('searched_at')) {
      context.handle(
        _searchedAtMeta,
        searchedAt.isAcceptableOrUnknown(data['searched_at']!, _searchedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_searchedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {query};
  @override
  RecentSearchRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return RecentSearchRow(
      query: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}query'],
      )!,
      searchedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}searched_at'],
      )!,
    );
  }

  @override
  $RecentSearchesTable createAlias(String alias) {
    return $RecentSearchesTable(attachedDatabase, alias);
  }
}

class RecentSearchRow extends DataClass implements Insertable<RecentSearchRow> {
  final String query;
  final String searchedAt;
  const RecentSearchRow({required this.query, required this.searchedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['query'] = Variable<String>(query);
    map['searched_at'] = Variable<String>(searchedAt);
    return map;
  }

  RecentSearchesCompanion toCompanion(bool nullToAbsent) {
    return RecentSearchesCompanion(
      query: Value(query),
      searchedAt: Value(searchedAt),
    );
  }

  factory RecentSearchRow.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return RecentSearchRow(
      query: serializer.fromJson<String>(json['query']),
      searchedAt: serializer.fromJson<String>(json['searchedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'query': serializer.toJson<String>(query),
      'searchedAt': serializer.toJson<String>(searchedAt),
    };
  }

  RecentSearchRow copyWith({String? query, String? searchedAt}) =>
      RecentSearchRow(
        query: query ?? this.query,
        searchedAt: searchedAt ?? this.searchedAt,
      );
  RecentSearchRow copyWithCompanion(RecentSearchesCompanion data) {
    return RecentSearchRow(
      query: data.query.present ? data.query.value : this.query,
      searchedAt: data.searchedAt.present
          ? data.searchedAt.value
          : this.searchedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('RecentSearchRow(')
          ..write('query: $query, ')
          ..write('searchedAt: $searchedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(query, searchedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is RecentSearchRow &&
          other.query == this.query &&
          other.searchedAt == this.searchedAt);
}

class RecentSearchesCompanion extends UpdateCompanion<RecentSearchRow> {
  final Value<String> query;
  final Value<String> searchedAt;
  final Value<int> rowid;
  const RecentSearchesCompanion({
    this.query = const Value.absent(),
    this.searchedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  RecentSearchesCompanion.insert({
    required String query,
    required String searchedAt,
    this.rowid = const Value.absent(),
  }) : query = Value(query),
       searchedAt = Value(searchedAt);
  static Insertable<RecentSearchRow> custom({
    Expression<String>? query,
    Expression<String>? searchedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (query != null) 'query': query,
      if (searchedAt != null) 'searched_at': searchedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  RecentSearchesCompanion copyWith({
    Value<String>? query,
    Value<String>? searchedAt,
    Value<int>? rowid,
  }) {
    return RecentSearchesCompanion(
      query: query ?? this.query,
      searchedAt: searchedAt ?? this.searchedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (query.present) {
      map['query'] = Variable<String>(query.value);
    }
    if (searchedAt.present) {
      map['searched_at'] = Variable<String>(searchedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('RecentSearchesCompanion(')
          ..write('query: $query, ')
          ..write('searchedAt: $searchedAt, ')
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
  late final $RecentSearchesTable recentSearches = $RecentSearchesTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    outboxMutations,
    cachedTitles,
    recentSearches,
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
typedef $$RecentSearchesTableCreateCompanionBuilder =
    RecentSearchesCompanion Function({
      required String query,
      required String searchedAt,
      Value<int> rowid,
    });
typedef $$RecentSearchesTableUpdateCompanionBuilder =
    RecentSearchesCompanion Function({
      Value<String> query,
      Value<String> searchedAt,
      Value<int> rowid,
    });

class $$RecentSearchesTableFilterComposer
    extends Composer<_$AppDatabase, $RecentSearchesTable> {
  $$RecentSearchesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get query => $composableBuilder(
    column: $table.query,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get searchedAt => $composableBuilder(
    column: $table.searchedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$RecentSearchesTableOrderingComposer
    extends Composer<_$AppDatabase, $RecentSearchesTable> {
  $$RecentSearchesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get query => $composableBuilder(
    column: $table.query,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get searchedAt => $composableBuilder(
    column: $table.searchedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$RecentSearchesTableAnnotationComposer
    extends Composer<_$AppDatabase, $RecentSearchesTable> {
  $$RecentSearchesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get query =>
      $composableBuilder(column: $table.query, builder: (column) => column);

  GeneratedColumn<String> get searchedAt => $composableBuilder(
    column: $table.searchedAt,
    builder: (column) => column,
  );
}

class $$RecentSearchesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $RecentSearchesTable,
          RecentSearchRow,
          $$RecentSearchesTableFilterComposer,
          $$RecentSearchesTableOrderingComposer,
          $$RecentSearchesTableAnnotationComposer,
          $$RecentSearchesTableCreateCompanionBuilder,
          $$RecentSearchesTableUpdateCompanionBuilder,
          (
            RecentSearchRow,
            BaseReferences<
              _$AppDatabase,
              $RecentSearchesTable,
              RecentSearchRow
            >,
          ),
          RecentSearchRow,
          PrefetchHooks Function()
        > {
  $$RecentSearchesTableTableManager(
    _$AppDatabase db,
    $RecentSearchesTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$RecentSearchesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$RecentSearchesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$RecentSearchesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> query = const Value.absent(),
                Value<String> searchedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => RecentSearchesCompanion(
                query: query,
                searchedAt: searchedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String query,
                required String searchedAt,
                Value<int> rowid = const Value.absent(),
              }) => RecentSearchesCompanion.insert(
                query: query,
                searchedAt: searchedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$RecentSearchesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $RecentSearchesTable,
      RecentSearchRow,
      $$RecentSearchesTableFilterComposer,
      $$RecentSearchesTableOrderingComposer,
      $$RecentSearchesTableAnnotationComposer,
      $$RecentSearchesTableCreateCompanionBuilder,
      $$RecentSearchesTableUpdateCompanionBuilder,
      (
        RecentSearchRow,
        BaseReferences<_$AppDatabase, $RecentSearchesTable, RecentSearchRow>,
      ),
      RecentSearchRow,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$OutboxMutationsTableTableManager get outboxMutations =>
      $$OutboxMutationsTableTableManager(_db, _db.outboxMutations);
  $$CachedTitlesTableTableManager get cachedTitles =>
      $$CachedTitlesTableTableManager(_db, _db.cachedTitles);
  $$RecentSearchesTableTableManager get recentSearches =>
      $$RecentSearchesTableTableManager(_db, _db.recentSearches);
}
