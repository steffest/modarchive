import os

from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from rest_framework import viewsets, generics, filters, pagination
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import F, Q
from django.http import HttpResponse, Http404

from songs.models import Song
from artists.models import Artist
from api.serializers.artist_serializers import ArtistSerializer
from api.serializers.song_serializers import SongDetailSerializer, SongListSerializer
from api.serializers.other_serializers import GenreSerializer

class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100

@extend_schema_view(
    list=extend_schema(
        description='Retrieve a list of songs. At least one filter must be provided: starts_with, license, genre or file_format',
        parameters=[
            OpenApiParameter("starts_with", OpenApiTypes.STR, description="Filter songs by first character of filename (single character)", required=False, location='query',),
            OpenApiParameter("license", OpenApiTypes.STR, description="Filter by license", enum=Song.Licenses, required=False, location='query',),
            OpenApiParameter("genre", OpenApiTypes.STR, description="Filter by genre", enum=Song.Genres, required=False, location='query',),
            OpenApiParameter("file_format", OpenApiTypes.STR, description="Filter by format", enum=Song.Formats.values, required=False, location='query',),
        ]
    ),
    retrieve=extend_schema(
        description='Retrieve a specific song'
    )
)
class SongViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Song.objects.all()
    pagination_class = StandardResultsSetPagination
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return SongListSerializer

        return SongDetailSerializer

    def get_queryset(self):
        qs = Song.objects.all()

        if self.action == 'list':
            starts_with = self.request.query_params.get('starts_with')
            license_val = self.request.query_params.get('license')
            genre = self.request.query_params.get('genre')
            file_format = self.request.query_params.get('file_format')

            # Require at least one of these four
            if not any([starts_with, license_val, genre, file_format]):
                raise ValidationError("At least one of 'starts_with', 'license', 'genre' or 'file_format' is required.")

            # starts_with must be single char
            if starts_with:
                if len(starts_with) != 1:
                    raise ValidationError("The 'starts_with' parameter must be a single character.")
                qs = qs.filter(filename__istartswith=starts_with)

            # license filter (validate against allowed choices)
            if license_val:
                allowed = [c for c in Song.Licenses.values]
                if license_val not in allowed:
                    raise ValidationError("Invalid license value.")
                qs = qs.filter(license=license_val)

            # genre filter (validate against allowed choices)
            if genre:
                allowed_genres = [c for c in Song.Genres.values]
                if genre not in allowed_genres:
                    raise ValidationError("Invalid genre value.")
                qs = qs.filter(genre=genre)

            # file_format filter (validate against allowed choices)
            if file_format:
                allowed_formats = [c for c in Song.Formats.values]
                if file_format not in allowed_formats:
                    raise ValidationError("Invalid file_format value.")
                qs = qs.filter(format=file_format)

        return qs

@extend_schema_view(
    list=extend_schema(
        description='List artists with optional filtering and ordering',
        parameters=[
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                description="Ordering field (ascending, add a '-' in front to sort descending)",
                required=False,
                location='query',
                enum=['name', 'id', 'total_songs', 'total_comments', 'total_downloads', 'average_song_rating'],
                default='name',
            ),
            OpenApiParameter(
                "starts_with",
                OpenApiTypes.STR,
                description="Filter artists by first character of name (single character)",
                required=False,
                location='query',
            )
        ]
    ),
    retrieve=extend_schema(
        description='Retrieve a specific artist'
    )
)
class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ArtistSerializer
    queryset = Artist.objects.all()
    pagination_class = StandardResultsSetPagination
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name', 'id', 'total_songs', 'total_comments', 'total_downloads', 'average_song_rating']
    ordering = ['name']

    def get_queryset(self):
        queryset = Artist.objects.all()

        if self.action == 'list':
            starts_with = self.request.query_params.get('starts_with')
            if starts_with:
                if len(starts_with) != 1:
                    return Artist.objects.none()
                queryset = queryset.filter(name__istartswith=starts_with)

        return queryset

@extend_schema_view(
    get=extend_schema(
        description='Search for songs with optional filtering. At least one of the following search parameters is required: title, filename, instrument_text, comment_text.',
        parameters=[
            OpenApiParameter("title", OpenApiTypes.STR, description="Search in song title", required=False, location='query'),
            OpenApiParameter("filename", OpenApiTypes.STR, description="Search in filename", required=False, location='query'),
            OpenApiParameter("instrument_text", OpenApiTypes.STR, description="Search in instrument text", required=False, location='query'),
            OpenApiParameter("comment_text", OpenApiTypes.STR, description="Search in comment text", required=False, location='query'),
            OpenApiParameter("min_file_size", OpenApiTypes.INT, description="Minimum file size in bytes", required=False, location='query'),
            OpenApiParameter("max_file_size", OpenApiTypes.INT, description="Maximum file size in bytes", required=False, location='query'),
            OpenApiParameter("min_channels", OpenApiTypes.INT, description="Minimum number of channels", required=False, location='query'),
            OpenApiParameter("max_channels", OpenApiTypes.INT, description="Maximum number of channels", required=False, location='query'),
            OpenApiParameter("file_format", OpenApiTypes.STR, description="Filter by file format", required=False, location='query', enum=Song.Formats),
            OpenApiParameter("genre", OpenApiTypes.STR, description="Filter by genre", required=False, location='query', enum=Song.Genres),
            OpenApiParameter("license", OpenApiTypes.STR, description="Filter by license", required=False, location='query', enum=Song.Licenses),
        ],
    ),
)
class SongSearchAPIView(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SongListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        title = self.request.query_params.get('title')
        filename = self.request.query_params.get('filename')
        instrument_text = self.request.query_params.get('instrument_text')
        comment_text = self.request.query_params.get('comment_text')

        if not any([title, filename, instrument_text, comment_text]):
            raise ValidationError("At least one of 'title', 'filename', 'instrument_text', or 'comment_text' is required.")

        # Parse min/max parameters
        min_file_size = self.request.query_params.get('min_file_size')
        max_file_size = self.request.query_params.get('max_file_size')
        min_channels = self.request.query_params.get('min_channels')
        max_channels = self.request.query_params.get('max_channels')

        def parse_positive_int(value):
            if value is None:
                return None
            try:
                val = int(value)
                if val <= 0:
                    return -1  # invalid
                return val
            except ValueError:
                return -1

        min_file_size = parse_positive_int(min_file_size)
        max_file_size = parse_positive_int(max_file_size)
        min_channels = parse_positive_int(min_channels)
        max_channels = parse_positive_int(max_channels)

        if min_file_size == -1 or max_file_size == -1 or min_channels == -1 or max_channels == -1:
            return Song.objects.none()

        if (min_file_size and max_file_size and min_file_size > max_file_size) or \
           (min_channels and max_channels and min_channels > max_channels):
            return Song.objects.none()

        file_format = self.request.query_params.get('file_format')
        genre = self.request.query_params.get('genre')
        license_filter = self.request.query_params.get('license')

        queryset = Song.objects.all()

        q_objects = Q()
        relevance_expr = 0

        if title:
            search_title = SearchVector('title_vector')
            rank_title = SearchRank(search_title, SearchQuery(title))
            queryset = queryset.annotate(search_title=search_title, rank_title=rank_title)
            q_objects &= Q(search_title=SearchQuery(title))
            relevance_expr += F('rank_title')

        if instrument_text:
            search_instrument = SearchVector('instrument_text_vector')
            rank_instrument = SearchRank(search_instrument, SearchQuery(instrument_text))
            queryset = queryset.annotate(search_instrument=search_instrument, rank_instrument=rank_instrument)
            q_objects &= Q(search_instrument=SearchQuery(instrument_text))
            relevance_expr += F('rank_instrument')

        if comment_text:
            search_comment = SearchVector('comment_text_vector')
            rank_comment = SearchRank(search_comment, SearchQuery(comment_text))
            queryset = queryset.annotate(search_comment=search_comment, rank_comment=rank_comment)
            q_objects &= Q(search_comment=SearchQuery(comment_text))
            relevance_expr += F('rank_comment')

        if filename:
            q_objects &= Q(filename__icontains=filename)

        if q_objects:
            queryset = queryset.filter(q_objects)
            if relevance_expr:
                queryset = queryset.annotate(relevance=relevance_expr).order_by('-relevance')

        # Apply additional filters
        if file_format:
            queryset = queryset.filter(format=file_format)

        if genre:
            queryset = queryset.filter(genre=genre)

        if license_filter:
            queryset = queryset.filter(license=license_filter)

        if min_file_size:
            queryset = queryset.filter(file_size__gte=min_file_size)

        if max_file_size:
            queryset = queryset.filter(file_size__lte=max_file_size)

        if min_channels:
            queryset = queryset.filter(channels__gte=min_channels)

        if max_channels:
            queryset = queryset.filter(channels__lte=max_channels)

        return queryset

@extend_schema(
    responses={
        200: OpenApiResponse(
            description="Zipped song file",
            response={'application/zip': {'type': 'string', 'format': 'binary'}}
        ),
        404: None
    },
    description="Download a song as a zip file"
)
class SongDownloadView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        # id = kwargs.get('id')
        song = Song.objects.get(pk=kwargs.get('pk'))
        
        local_file_path = song.get_archive_path()

        if not os.path.exists(local_file_path):
            raise Http404("File not found")

        stats = song.get_stats()
        stats.downloads = F('downloads') + 1
        stats.save()

        # Serve the file as a response
        with open(local_file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{song.filename}.zip"'
            return response

@extend_schema_view(
    get=extend_schema(
        description='Get a list of available genres'
    )
)
class GenreListAPIView(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = GenreSerializer

    def list(self, request, *args, **kwargs):
        genres = [{'id': value, 'text': label} for value, label in Song.Genres.choices]
        serializer = self.get_serializer(genres, many=True)
        return Response(serializer.data)

@extend_schema_view(
    get=extend_schema(
        description="Search for artists by name, ordered by search relevance",
        responses={200: ArtistSerializer},
        parameters=[
            OpenApiParameter("name", OpenApiTypes.STR, description="Search by artist name", required=True, location='query'),
        ],
    )
)
class ArtistSearchAPIView(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ArtistSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        name = self.request.query_params.get('name')

        if not name:
            raise ValidationError("The 'name' parameter is required.")

        queryset = Artist.objects.annotate(
            rank=SearchRank('search_document', SearchQuery(name))
        ).filter(
            search_document=SearchQuery(name)
        ).order_by('-rank', 'name')

        return queryset


@extend_schema(
    responses={200: SongListSerializer},
    description="Retrieve a list of songs by artist",
    parameters=[]
)
class ArtistSongsListAPIView(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SongListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        artist_id = self.kwargs.get('pk')
        artist = get_object_or_404(Artist, pk=artist_id)

        # Try common reverse relation names on Artist to fetch songs

        if hasattr(artist, 'songs'):
            manager = getattr(artist, 'songs')
            try:
                return manager.all()
            except TypeError:
                # If it's a queryset/manager-like already
                return manager
        return Song.objects.none()